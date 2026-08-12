# Rules as a reference layer over nodes — a fundamental re-review

**Status: SPIKE. No code, no seeds, no runs, no builds in this document.** One
new file; nothing else in the repository is touched. Written against `main` at
`9b775cf` (verified: `git log --oneline -1 main` → `9b775cf Merge
chunk-equivalence: P7C residual #8, NO-GO, measured not assumed`).

**Charter, quoted verbatim from the project's creator, because everything below
is an attempt to answer exactly this and nothing wider:**

> "The problem is that rules do not have a shape. Should rules in fact be a
> reference layer over nodes?" … "I think I may have started this or talked
> about it at some point, but it is inevitable and essential — the rules engine
> makes sense, but they need to exist as nodes with shape, because the shape
> math gives all of the things that are missing. Treat this as a fundamental
> re-review of how rules work — While we need things to work, the ideal design
> shouldn't be beholden to previous decisions. The better design is what we
> need to target."

Confidence is flagged throughout. Claims I verified by reading the source in
this tree carry file:line citations. Claims I did not independently re-verify
are marked `[unverified]`. Everything in §3 is measurement I ran myself against
this tree today; everything in §4 is text I actually fetched and read from the
creator's private research repo, quoted where the wording matters.

**My one-line answer, up front, so a reader can stop here if that is all they
want:** *yes, qualified* — and the qualification is not about whether rules
should have shape (they should, and the evidence that they currently do not is
much sharper than I expected) but about **which half of a rule the reference
layer is for**. A rule's `match`/`where` is a *recogniser* and belongs in the
subsumption lattice the sd loop already runs. A rule's `effects` is a
*constructor* and belongs on the other side of the same lattice — it is not
shapeless, but it is a `Substitute`/instantiate object, not a `Covers`/recognise
object, and a design that files both under one undifferentiated "rule shape"
will get the effects half wrong. §8 works this through.

---

## 1. What this document is, and what it is not

This is a design spike, in the sense
`docs/research/engine_substrate/decision_making_spike.md` uses the word: a
first-person research journal, written before any build, whose job is to make
the design decision *legible and falsifiable* rather than to make it.

It is organised in three parts, mirroring the charter:

* **Part 1 (§2–§3)** — ground the diagnosis. Does the creator's claim ("rules do
  not have a shape") hold against the code that is actually in this tree today?
  I treated this as a claim to be checked, not a premise to be elaborated. It
  holds, and in a sharper form than the brief that reached me stated. It also
  contains one factual correction to that brief (§2.1).
* **Part 2 (§4)** — the creator's own prior thinking, from the private research
  repo, read rather than re-derived. The most important finding here is that the
  *algebra* this design needs was researched in June 2026 **and then built** —
  four Rust Terms that are in `term.rs` right now and are, as far as I can
  measure, unused by the rule layer.
* **Part 3 (§5–§10)** — the actual design, question by question, followed by an
  honest cost sizing (§10) and an explicit out-of-scope boundary with a named
  smallest-first-slice (§11).

§12 states what this document does **not** establish. §13 is the reproduction
recipe for every number in §3.

**What this document is not:** a build plan, a phased roadmap, a schedule, or a
commitment. It does not propose that anything be built. Per the project's own
culture I have tried to size the work honestly (§10) precisely so that the
decision *not* to build it stays available.

---

## 2. Part 1 — the diagnosis, checked against the code

I read the three pieces of evidence the brief named, plus the Rust they point
at, plus a fourth and fifth thing I found while checking them. Six findings
follow. Five confirm the creator's claim; one corrects a detail of how the claim
reached me.

### 2.1 CORRECTION: Rule bodies do **not** round-trip as `Term.*` subgraphs. Γ productions do. The brief had this backwards.

The brief I was given asserted, as an established fact to verify:

> `graph_rules.rs`'s `rule_from_node`/Rule bodies DO round-trip as real graph
> subgraphs via `reflect::term_to_subgraph`/`term_from_subgraph` — so a Rule's
> match/where/effects Terms CAN decompose into real, individually-addressable
> graph nodes (`Var`, `Attr`, `Exists`, `Lit`, etc.) — this is NOT hypothetical,
> it already works.

**This is false for Rules, and I want it corrected in the record before any
design is built on it.** I read every call site of `term_to_subgraph` /
`term_from_subgraph` in `runners/dsl/src/`. There are exactly four
non-test, non-doc callers:

| caller | what it reflects | file:line |
|---|---|---|
| `grammar_reflect::production_to_subgraph` | a Γ `Production`'s `where_` and `weight` | `grammar_reflect.rs:105`, `:114` |
| `grammar_reflect::production_from_node` | the same, read back | `grammar_reflect.rs:223`, `:228` |
| `prog_eval` (Program-IR `EvalSubgraph`) | a program's own IR | `prog_eval.rs:2038`, `:2766` |
| `PySubstrate::add_term_subgraph` (+ the seed loader's `"reflexes"` key) | an arbitrary Term, on demand; a Reflex's `stimulus` Term | `py.rs:8530`; `py.rs:1642-1656` |

**`graph_rules.rs` is not among them.** A graph-resident Rule node's body is read
by `rule_from_node` (`graph_rules.rs:362-428`) straight off three *attributes*:

```rust
let match_v  = attrs.get(&match_sym)?.clone();      // graph_rules.rs:384
let where_v  = attrs.get(&where_sym).cloned()...;   // graph_rules.rs:385
let effect_v = attrs.get(&effect_sym)?.clone();     // graph_rules.rs:386
```

and `parse_where` (`graph_rules.rs:134-153`) converts that one attribute Value
into `serde_json` via `value_to_json` and then into a Term via
`term_from_json`. So a Rule's where-clause lives as **one nested
`Value::Dict`/`Value::Tuple` blob hanging off a single attr key** — an opaque
payload as far as the graph is concerned. There is no `Term.Exists` node, no
`Term.Attr` node, no `child.predicate` edge. Nothing in the graph can match on
"every rule that reads attribute `status`", because the string `"status"` is
buried inside an attribute value, not present as a node.

The other Rule population — `Substrate::rules`, the persistent
`Vec<RewriteRule>` — is even further from graph-native: `Substrate::add_rule`
(`substrate.rs:2480-2560+`) pushes a compiled struct into a Rust `Vec` and
**writes no graph node at all**.

**Why the correction matters for the design and not just for the record:** the
brief's framing implied the reference layer is mostly a matter of *wiring up*
something that already decomposes. It is not. The Γ side already decomposes
(§2.1's table, row 1) — the **Rule** side, which is where essentially all of the
agent's cognition lives, does not. This is a genuine inversion: the layer that
`SELF_REFERENCE_INFINITY_GROUNDING.md` §3.3 correctly called out as *"genuinely
graph-native… a rule editing a rule"* is graph-native at the level of *the rule
node's identity and lifecycle*, and opaque at the level of *the rule's body*.
That distinction is the whole subject of this document.

Confidence: **high**. I read all four call sites and `rule_from_node` directly.

### 2.2 Nothing deduplicates or canonicalises. Verified at both levels.

The brief asked me to confirm this precisely rather than assume it, and to
report if I found dedup logic that already exists. **I found none, at either of
the two places it could live.**

**Term arena (Rust-internal).** `TermArena::add` (`term.rs:2222-2226`) is a pure
append:

```rust
pub fn add(&mut self, node: TermNode) -> TermIdx {
    let idx = TermIdx(self.nodes.len() as u32);
    self.nodes.push(node);
    idx
}
```

No hash-consing, no structural interning, no lookup of an existing identical
node. Two syntactically identical subterms parsed at different times occupy two
distinct arena slots. (Symbols *are* interned — `Interner` — so *strings* are
shared; *structures* are not.)

**Graph reflection.** `reflect::term_to_subgraph` (`reflect.rs:45-121`) calls
`graph.insert_node(type_sym, attrs)` unconditionally at line 107, recursing to
`term_to_subgraph` for each child at lines 89/94/100. There is no find-or-create
path, no content key, no lookup. Reflecting the same Term twice yields two
disjoint isomorphic subgraphs. `grammar_reflect::production_to_subgraph`
(`grammar_reflect.rs:57-121`) inherits this: every `add_production` mints a fresh
`GammaProduction`, two fresh `GammaNodePattern`s, and a fresh Term subgraph for
`where_` and for `weight` — even when an identical production shape already
exists in the graph. `GAMMA_REFLECTION_WIRING_RESULTS.md` §5 documents this as an
observed side effect (the mirror "now allocates real graph nodes too", shifting
NodeIDs by 5 per production) without ever framing it as an absence of sharing —
which it also is.

I grepped for `dedup`, `canonical`, `hash-cons`/`hashcons` across
`runners/dsl/src/*.rs` and cross-checked every hit. The only relevant hits are:

* `Effect::AddNodeIfAbsent` (`graph_rules.rs:261-277`) — find-or-create for
  *world* nodes by author-supplied attrs, not for Term structure;
* `Substrate::rule_content_hash` (`substrate.rs:2229-2247`) — FNV-1a over the
  whole serialised rule body, minus install metadata. This is an **all-or-nothing
  identity**: two rules that differ in one literal hash completely differently.
  It supports CAS on rule patches; it cannot support partial sharing, similarity,
  or lattice position;
* `substrate/rule_ir.py::canonical_rule_body` — a Python canonicaliser used for
  *change detection* on daemon resume (`scripts/jabberwock_daemon.py:550-565`).
  Its own docstring is explicit that the result "is diagnostic data and must not
  be installed as a rule."

So there is prior art for *"is this the same rule?"* (exact, boolean) and none
at all for *"is this the same shape?"* (graded, structural). That gap is exactly
the charter.

Confidence: **high** for the arena and reflection findings (read directly);
**high** for "no other dedup exists" modulo the usual limits of a grep-plus-
spot-check sweep — I checked every hit I found, but I cannot prove a negative
over 22k lines of Rust.

### 2.3 `covers_value`'s equal-length requirement — and the asymmetry that is the escape hatch

`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` traced residual #8 to
`covers_value` requiring equal-length relation lists. Verified —
`term.rs:3711-3739`:

```rust
Value::Tuple(pt) | Value::List(pt) => {
    let (Value::Tuple(it) | Value::List(it)) = inst else { return false };
    pt.len() == it.len()                                       // term.rs:3727
        && pt.iter().zip(it.iter()).all(|(p, i)| covers_value(p, i, wild))
}
```

`anti_unify_values` has the mirror-image constraint (`term.rs:3341-3355`): all
tuples must be the same length `n`, else the whole comparison falls through to
`WILD`. Both are exactly as the results doc reports.

**But the same function has a length-free arm three lines further down, and I
have not seen this named anywhere:**

```rust
Value::Set(ps) | Value::FrozenSet(ps) => {
    let is = match inst { Value::Set(s) | Value::FrozenSet(s) => s, _ => return false };
    ps.iter().all(|m| is.iter().any(|x| x == m))               // term.rs:3735
}
```

A **set** pattern covers an instance by *subset*. No length equality. The
equal-length trap is not a property of `Covers` — it is a property of encoding a
relation-system as a *positional Tuple* rather than as a *set of
path-addressed rows*. `chunk_rels` is a positional list
(`["ckstmt", i, label]` / `["ck", i, path, atom]`, where `i` is a statement
index — see the real held entry in `seeds/mbpp_train_diet.json`), so its rows are
order- and count-coupled by construction, and `ShapeDecode`'s own JSON decoder
turns a bare JSON array into `Value::Tuple` (`shape_decode.rs`,
`json_to_value_scoped`, the `Array` arm), which lands on the equal-length arm.

This is a **representational** cause, not an engine limitation, and it is
directly load-bearing for §9. It also means one of the two mechanisms the
chunk-equivalence rung offered ("extend `Covers`") was arguably the *wrong*
mechanism even in the abstract: `Covers` already has the semantics; the
signature encoding does not use them.

Confidence: **high** on the code reading. **Medium** on "changing the encoding
would have rescued residual #8 specifically" — that rung's NO-GO was decided on
*prevalence* (0 corpus payoff), not on mechanism, so this observation does not
overturn its verdict and I am not claiming it does. It changes what a *future*
rung would build, not what that one should have.

### 2.4 The same defect at the chunk grain — a second, independent instance

`ckg_recognize` (`seeds/prog_chunk_growth.json`, mechanism documented in
`domains/prog_chunk_growth.py:31-34`) decides idiom recognition via the engine
`Covers` Term over `chunk_rels`. It therefore inherits §2.3 exactly: two program
idioms of different statement count can never match, however equivalent.

That is the "rule" problem one grain up: a *pattern* is compared to an *instance*
by literal re-derived positional structure. The brief asked me to name this as a
second instance of one root cause rather than a separate bug, and I agree — with
one addition. It is not two instances, it is **at least four**, and the fourth is
the sharpest (§2.5).

### 2.5 The sharpest finding: a rule's "shape", today, is literally its name

This is the finding I did not expect and consider the strongest single piece of
evidence for the creator's claim.

The agent's self-improvement machinery has to answer, repeatedly, *"which of my
rules is the one this concern is about?"* It answers it through
`RuleSummary` nodes minted by `_ensure_acting_rule_provenance`
(`domains/reflective_faculty.py:2615-2701`). Here is the mint, verbatim
(`reflective_faculty.py:2689-2698`):

```python
sub.add_node("RuleSummary", {
    "name": name,
    "keywords_text": name.replace("_", " "),
    "writes_chosen_action": 1.0,
    "shift_count": float(len(thresholds)),
    "shiftable": 1.0 if thresholds else 0.0,
    "rule_json": _json.dumps(r),
    "from_seed": from_seed,
    "skippable": skippable,
})
```

And here is how it is used — `_pick_acting_rule`
(`reflective_faculty.py:2704-2765`) builds an `Argmax` over `RuleSummary` nodes
scored by:

```python
overlap = lambda node_t: Sum(words, "w",
    Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
```

**The agent selects which of its own rules to vary by counting substring hits
between the concern's residual predicate words and the rule's own name with
underscores replaced by spaces.** The rule's body is present only as
`rule_json`, an opaque JSON *string*.

Three further observations sharpen this rather than soften it:

1. `writes_action` (`reflective_faculty.py:2672-2675`) gates whether a
   `RuleSummary` is minted at all — only rules whose effects contain
   `set_attr … "chosen_action"` get one. Two more provenance minters exist for
   two more questions: `_ensure_reply_rule_provenance`
   (`reflective_faculty.py:2873`) and `_ensure_where_literal_rule_provenance`
   (`reflective_faculty.py:3445`). **Three bespoke mirrors, each with its own
   hand-written boolean flag, because there is no shape to ask a question of.**
   A fourth question needs a fourth mirror.
2. The *site selection* inside a picked rule — which comparison, which attr key
   — is done by hand-written recursive Python tree-walkers:
   `edit_ops.find_comparison_nodes` (`domains/edit_ops.py:49-70`),
   `edit_ops.find_attr_keys` (`:72-95`),
   `self_correction._find_identity_eq` (`domains/self_correction.py:286-313`),
   `reflective_faculty._find_threshold_lits` (`:2529`), `_find_where_lits`
   (`:3298`), plus a duplicate of the first in `domains/self_model.py:165`.
   `_find_identity_eq`'s docstring names what it is doing with unusual candour:
   *"the SHAPE `seeds/shape_decode_loop.json`'s `sd_mint_quantum` novelty guard
   … carries"* — it is looking for a **shape**, by hand, in Python, one shape per
   function.
3. This is precisely the failure mode the creator's own research diagnosed for a
   *different* faculty two months earlier. See §4.2 — `find_analogies` was
   diagnosed as "the MAC stage treated as the verdict, with no FAC stage." A
   name-keyword `Argmax` over `RuleSummary` **is a MAC stage**. There is no FAC
   stage for rules; the structural half is hand-written per question.

Confidence: **high**. Read directly; both call chains traced.

### 2.6 The bespoke-Term tax — three Rust Terms that exist only because rule bodies are opaque

Because a rule body is a `Value` blob rather than addressable structure, every
new structural question about a rule has needed **its own Rust primitive**. All
three are real, shipped, and documented as exactly this:

| Term | what it does | why it exists (its own doc comment) | file:line |
|---|---|---|---|
| `ShiftThresholdLits { tree, shift }` | walk a Value tree, shift every `Lt`/`Gt` comparison's `Lit` | *"the graph-native primitive that was missing for a meta-rule to do the same rewrite itself instead of calling out to a host Python helper"* | `term.rs:194` (doc `:178-193`) |
| `RewriteTreeNodes { tree, type_filter, field, value_map }` | walk a Value tree, remap one field where a node's `type` matches | *"The general conditional-tree-rewrite primitive `domains/edit_ops.py`'s two effects-only structural appliers need"* | `term.rs:247` (doc `:211-246`) |
| `AttrKeyRanking { tree }` | frequency-rank every `Attr` node's `key` in a tree | *"the one missing primitive `apply_swap_term_leaf`'s composition needed to go fully graph-native"* | `term.rs:275` (doc `:249-274`) |

Plus the supporting cast that exists to get *into* and *out of* the blob:
`FromJsonString` (`term.rs:176`, whose doc explicitly names *"a
`RuleSummary.rule_json` mirror"* as its motivating caller), `ToJsonString`
(`:161`), `DictGet` (`:209`, added because *"reading a parsed rule's own
`match`/`where`/`effects` fields back out of the `FromJsonString` result has no
other route through the existing dialect"*).

**Under a reference layer, all six of these are ordinary graph queries.**
`AttrKeyRanking` is `Count` grouped over `NodesOfType("Term.Attr")` reachable
from a rule; `RewriteTreeNodes` is `Substitute` with a σ; `ShiftThresholdLits` is
a `Transform{dim, delta}` in the sense CLAUDE.md's "Transformation = quantum
change in a specific dimension" section already defines; `FromJsonString` /
`ToJsonString` / `DictGet` disappear entirely because there is no blob to parse.

This is the same pattern CLAUDE.md's SHAPES-NOT-NUMBERS section describes one
level up. There, a subsystem invents a scalar knob where a shape belonged. Here,
a subsystem invents a **special-purpose Rust Term** where a shape belonged — and
the regress is the same: each new structural question needs its own Term, and
each new Term needs its own composition idiom, and the composition idiom needs
`IndexAt(IndexAt(ranking, 0), 0)` (`term.rs:265-266`, quoted from the doc
comment) to read it back.

Confidence: **high** on what the Terms do and why (their own doc comments say
so). **Medium** on "all six become ordinary queries" — that is my design claim,
argued in §7, not a measured fact.

Also worth naming here because it is *nearly* the thing being asked for and is
instructive precisely for how it falls short: `runners/dsl/src/shape.rs` already
defines a struct called `Shape` for a Term-tree — three scalar axes
(`RecursionKind`, `OrderN(u8)`, `AbstractionKind`; `shape.rs:50-97`), cached in
`Substrate::shape_cache` (`substrate.rs:148`), exposed to Python as
`add_shape_node_for_term` / `shapes_compatible` (`py.rs:8497`, `:8564`). It is a
**feature vector**, not a structure: `{none|direct|structural} × u8 ×
{concrete|parametric}`. Two rules with identical three-axis Shape can be
arbitrarily different. It is, in CLAUDE.md's own vocabulary, three numbers where
a shape belongs. I read this as prior art that got the *word* right and the
*object* wrong, and I say so in §5.

---

## 3. Part 1, continued — measuring how much shape there is to share

The diagnosis above is qualitative. Before designing anything I wanted a number,
because "rules repeat structure" is the kind of claim that sounds obviously true
and can be wrong by an order of magnitude in either direction.

**Method.** Read-only scan over every `seeds/*.json` manifest in this tree
(893 files at top level). For every entry under a manifest's `"rules"` key that
carries both `match` and `effects` (2,934 of 4,107 entries — the other 1,173 are
microtheory entries keyed `head`/`body` or `if`/`then`/`why`, which carry no
Term-tree and contribute nothing), walk every Term-JSON node reachable from the
`where` clause and from every `{"__term__": …}` computed effect argument. Count
distinct subtrees under three canonicalisations: **exact** (byte-identical
Term-JSON, key-sorted), **alpha** (Var names renamed positionally per subtree),
**alpha+lit** (alpha, plus every `Lit` value wildcarded). Script and recipe in
§13. Nothing is mutated; the script lives in scratchpad and is not committed.

**Headline.**

| | count |
|---|---|
| executable rules scanned | **2,934** |
| Term-JSON nodes in their bodies | **925,002** |
| distinct subtrees, exact | 49,846 — **18.56×** repetition |
| distinct subtrees, alpha-renamed | 36,155 — **25.58×** |
| distinct subtrees, alpha + literals wildcarded | 32,908 — **28.11×** |

**One idiom accounts for 16.1% of all of it.** The pattern
`Plus(Attr(?v, k), Lit(0.0))` — "read this attribute as a float, defaulting to
zero" — occurs **149,276 times** out of 925,002 Term nodes. Under the current
design each of those 149,276 occurrences is freshly parsed into its own arena
slots on every tick that reaches it (per-tick arena: `graph_rules.rs:453`,
`run_graph_rules_opts` builds a fresh `TermArena::new()` each call and reparses
every rule).

**Now the honest half, because the headline is not evenly distributed.** Term
mass by seed file:

| seed file | Term nodes | share | rules |
|---|---|---|---|
| `embodied_motor_program.json` | 427,584 | **46.2%** | 43 |
| `humanoid_adaptation.json` | 122,802 | 13.3% | 128 |
| `helicopter_autorotation.json` | 75,510 | 8.2% | 16 |
| `embodied_adaptation.json` | 34,813 | 3.8% | 15 |
| `precision_driving.json` | 29,508 | 3.2% | 6 |

The top three files are 67.7% of the total, and all of them are the numeric
embodied seeds. Restricting to the conversation/cognition family (58 files whose
names carry `conversation`/`gap_`/`intent`/`anaphora`/`pronoun`/`referent`/
`question`/`self_`/`topic`/`elaborat`/`teach`/`reflect`/`psych`/`relation`/
`comprehen`), the picture is far more sober:

| | count |
|---|---|
| rules | 217 |
| Term nodes | 5,683 |
| distinct, exact | 2,211 — **2.57×** |
| distinct, alpha | 1,791 — **3.17×** |
| distinct, alpha+lit | 1,476 — **3.85×** |

And the `composer_*_graph.json` family (19 files, 22 `Rule` *nodes* carried as
graph data rather than as manifest rules — the agent's own rule-authoring
meta-rules): 2,344 Term nodes, 564 distinct alpha — **4.16×**.

**How I read these three numbers together.** The 18–28× figure is real but it is
a fact about the numeric embodied seeds, and quoting it bare would be exactly
the error CLAUDE.md's retracted-optional-dep-note section warns about (a
condition-dependent number quoted without its condition). The number that
matters for the *cognition* the charter is about is **2.6–3.9×**, and for the
agent's own rule-authoring layer **4.2×**. Those are worthwhile but they are not
transformative on compression grounds alone.

**Which is itself the interesting result.** If the case for a reference layer
rested on storage compression, it would be a weak case outside the embodied
seeds. It does not rest on compression — it rests on §2.5 and §2.6, on the
*queries that become possible*, not on the bytes saved. I flag this explicitly
because it is the point at which I most expected to talk myself into the design
and had to stop.

One structural number that *is* uniform across families and does bear on the
design: **1,599 distinct alpha-renamed match-edge shapes across 2,934 rules
(1.83×), of which 1,178 are singletons.** The single most common shape,
`(?0 -observed-> ?1)`, is shared by 66 rules; `(?0 -has_goal-> ?1)` by 42. So the
*match* clause is genuinely near-unique per rule while the *where* clause is
heavily repetitive — which, as §6 works out, is a real asymmetry the design
should exploit rather than paper over.

Confidence: **high** on the counts (deterministic scan, recipe in §13).
**Medium** on the family split being the right cut — "conversation/cognition"
is a name-substring heuristic I chose, not a declared seed taxonomy, and a
different cut would move the 2.6–3.9× figure somewhat. It would not move it to
18×.

---

## 4. Part 2 — the creator's own prior work, read

I fetched and read five things from `ozmalabs/internal`
(`research/experiments/gamma-substrate/`). The most important finding is in
§4.1 and it is not what I was told to expect.

### 4.1 `docs/shape_math_grounding.md` — the algebra was researched, and then it was BUILT

This is the creator's 2026-06-27 literature spike into "SHAPE MATH — operating
ON shapes", framed as *"the missing piece after order-N shape MATCHING."* Its
four clusters (proportional analogy / the subsumption lattice / vector analogy
as a lossy contrast / conceptual blending) converge on one actionable:

> **The subsumption LATTICE (exact framing):** terms ordered by "more general
> than"; **anti-unification = MEET (glb), unification = JOIN (lub).** So
> **"X but with Y" = move DOWN the lattice (instantiate via SUBSTITUTE),
> "abstract X out / vice versa" = move UP (anti-unify).**

and names three likely-missing primitives:

> (1) **AntiUnify returning its WITNESS substitutions** (the difference,
> currently latent); (2) **SUBSTITUTE / instantiate**…; (3) **Covers-with-witness
> / MATCH**…; and the constructive (4) **UNIFY / amalgam**.

with the instruction that *"the agent should CHECK its held Terms — it may
already hold Unify/Substitute, as it already held AntiUnify."*

**I checked. Three of the four were subsequently built, and they are in this
tree right now.** `runners/dsl/src/term.rs`:

* `AntiUnifyWitness { values, wild }` — `term.rs:833`. Doc, `term.rs:824-832`:
  *"Anti-unification that RETAINS its WITNESSES — the lattice-MEET that also
  emits the DIFFERENCE… returns a 2-Tuple `(template, sigmas)`… The residue
  `AntiUnify` discards, captured: the difference Y in 'this is like X but with
  Y'."* That is the grounding doc's item (1), implemented, with the doc comment
  quoting the grounding doc's own phrase.
* `Substitute { template, sigma, wild }` — `term.rs:844`. Doc: *"the lattice-JOIN
  direction… This REALISES 'X but with Y' (move DOWN the subsumption lattice) and
  inverts decompose."* That is item (2).
* `Unify { values, wild }` — `term.rs:858`. Doc: *"the lattice JOIN (lub), the
  constructive DUAL of `AntiUnify`… The Fauconnier-Turner blend / Ontañón-Plaza
  amalgam over the generic `AntiUnify` already computes."* That is item (4),
  down to the citations.
* Plus one the grounding doc did not name: `StructSim { a, b, wild }` —
  `term.rs:872`, a graded structural similarity in [0,1] with soft numeric-vector
  leaves and exact string/atom leaves.

Item (3), `Covers`-with-witness, appears **not** to have been built — `Covers`
(`term.rs:822`) still returns a boolean, and I found no `CoversWitness` variant
in the 211-entry variant table (`term_variants.rs:15`, `NUM_TERM_VARIANTS = 211`).
`[unverified]` — I searched the variant list and grepped for `Witness`; I did not
exhaustively read all 211 doc comments.

**This is the single most consequential finding in Part 2, and it reframes the
whole question.** The charter says *"the shape math gives all of the things that
are missing."* The shape math is **already here**. What is missing is not the
algebra — it is that **the rule layer has no object for the algebra to operate
on**. `AntiUnifyWitness` can take the meet of two structures and hand back the
difference; there is no addressable structure for a *rule* to hand it. So the
question "should rules be a reference layer over nodes?" is, read precisely:
*should a rule's body become the kind of object the already-built shape math can
already take?*

Put that way I find the answer close to forced, and the design work (Part 3)
becomes much narrower and much more concrete than "invent a shape system."

Confidence: **high** on the four Terms existing with those semantics (read the
doc comments and the variant table). **Medium** on "the rule layer never uses
them" — I grepped for `AntiUnifyWitness`/`Substitute`/`Unify` across `seeds/` and
`runners/dsl/src/` and found the shape-decode/ink/composer paths but no rule-body
caller; I did not audit every seed.

### 4.2 `docs/order_n_shape_matching_grounding.md` — the rule layer has the *identical* diagnosed defect

This is the 2026-06-27 spike into structure-mapping (Gentner; SME; MAC/FAC). Its
diagnosis of the agent's `analogical_thinking.find_analogies`:

> **MAC/FAC** = two stages: **MAC** = cheap, non-structural **content-vector
> dot-product** … **FAC** = expensive **SME structural alignment** on the few
> survivors. KEY DIAGNOSIS: **the agent's bucket IS the MAC stage treated as the
> verdict — with no FAC stage.**

and its prescription:

> FIX: make the bucket a **FILTER, not a verdict** — escalate every surface
> survivor into an explicit structural-alignment pass gated by parallel
> connectivity + systematicity.

Read §2.5 against that paragraph. `_pick_acting_rule`'s
`Sum(StringIndexOf(keywords_text, w))` **is a content-vector dot product**. It is
a MAC stage. It is treated as the verdict — the `Argmax`'s winner is the rule
that gets varied. There is no FAC stage; where structure genuinely has to be
consulted, it is consulted by hand-written Python walkers (§2.5 item 2). **The
defect the creator diagnosed for concept-analogy in June is, verbatim, the
defect the rule layer has today, and nobody appears to have noticed it is the
same defect** — presumably because it does not look like an analogy problem, it
looks like a "which rule do I edit" problem.

Two further things from this document are directly load-bearing for Part 3:

> **Relations as FIRST-CLASS NODES** (reified relation-nodes / hyperedges): a
> relation can be an ARGUMENT to another relation → **order-N for free on the
> graph, no new machinery**.

and

> **Order-N as a FIXPOINT of the agent's own shape-matcher applied to its own
> outputs:** compare → extract the surviving invariant → predicate it as a
> relation-node → compare predicates → order-(N+1). Comparison IS the
> relation-builder.

The second is, almost word for word, what a rule-shape codebook growing under
the sd loop *is* (§7). The first is the mechanism (§6).

Confidence: **high** — direct quotation from the fetched text.

### 4.3 `scripts/rule_lift.py` / `domains/rule_lifter.py` — a different problem, and it is already in this tree

The brief asked me to read these and correctly distinguish them. They are a
**mechanical AST lifter**: recognise a narrowly-shaped Python function
(`for n in substrate.nodes("T"): if <attr condition>: substrate.set_attr(...)`)
and emit an equivalent graph-resident Rule, live, with no maturin rebuild.
`rule_lifter.py`'s docstring is explicit that the recognised subset is
"RESTRICTED, well-defined" and that "a near-miss is None, never a wrong Rule."

**This is a translation tool: Python → Rule.** It says nothing about what a Rule
*is* once it exists, and gives a Rule no shape. Conflating it with the present
question because both contain the word "rule" would be a real error; the brief
was right to warn about it.

Worth noting for the record: both files **already exist in this repository**
(`domains/rule_lifter.py:347` `recognize_rule_shape`, `scripts/rule_lift.py`) —
they were ported across, not left in the research repo. The function name
`recognize_rule_shape` is a false friend: it recognises whether a *Python
function* has a liftable shape, not whether a *Rule* has a shape.

Confidence: **high**.

### 4.4 `scripts/jabberwock_designs_rule_index.py` — the agent's own prior proposal, and the honest gap

I read this in full. It is a capture harness with no design text of its own —
its docstring says so: *"I frame ONLY the concern; the agent's `induce_concern`
(shape-decode loop), `categorise_by_shape` (its seven meta-shapes), and
`ground_concern` (its composer registry) do the recognizing. No design text is
written here. Verbatim capture only."*

The concern it frames to the agent is, verbatim (`rule_index.py:47-52`):

```python
concern = [
    ["scan", "EVERY", "RULE", "per", "EVENT"],
    ["match", "over", "the", "WHOLE", "FRAME", "SET"],
    ["gate", "the", "SCAN", "to", "the", "FOCUS"],
    ["decode", "only", "the", "RULES", "in", "FOCUS", "for", "this", "TYPE"],
]
```

and its four probes ask: which of the seven meta-shapes does the agent file this
under; does its composer registry have a path to author the fix or is it an
honest wall; and what held parts does `ShapeDecode` decompose the concern into.

**I could not find any captured output.** I listed
`research/experiments/gamma-substrate/results/` and `…/docs/` in full and
grepped both listings for `rule_index`, `rule_scan_foveation`, `RuleScanConcern`;
GitHub's code-search API returned nothing for all three. The three `*index*.json`
artefacts that do exist (`dirty_index.json`, `locality_index.json`,
`fixpoint_rerun_index.json`) are rule-matching *performance* measurements —
dirty-bit skip fractions, spatial-locality benchmarks, per-script `run_rules`
call counts and "harmful skips" — i.e. they are results from the *engineering*
answer to the same performance concern (index the scan), not from the agent's
own design proposal. **I am reporting this as an honest null**: the agent's own
words on this question, if they were ever captured, are not in the places I
could reach.

What I take from the script itself, which is still worth something: the concern
as framed is a **foveation / selective-gating** concern — "decode only the rules
in focus for this type" — and the creator deliberately routed it through
`induce_concern`/`ShapeDecode`, i.e. through the sd loop, rather than through a
performance-engineering frame. That is a strong prior that the creator already
saw rule-selection as a *decode* problem in June, which is exactly the shape of
§7 below. But it is a prior, not evidence, and I am not going to dress it up as
the agent having proposed this design.

Confidence: **high** that no capture exists in the two directories I enumerated;
**medium** that none exists anywhere in that repo (I could not search the whole
repo's history, and the code-search API returned empty for queries I would have
expected to hit *something*, which makes me suspect the index rather than the
absence).

### 4.5 The rest, briefly

* `docs/shape_generation_grounding.md` — "a shape = the trajectory of a
  residual-feedback recurrence: `state_{n+1} = Substitute(state_n, σ_n)`". Its
  opening line confirms §4.1 from the other direction: *"The agent now holds the
  full shape-math algebra (AntiUnify=MEET, AntiUnifyWitness=extract residual σ,
  Substitute=apply σ, Unify=JOIN/blend)."* Relevant to §7's "growth is a
  recurrence" framing; not otherwise on point.
* `docs/function_shape_prior_work.md` — the lineage behind `shape.rs`. Its three
  stated needs are *cache* higher-order shapes, *generic* order-N, *classify*
  every function by {recursion, order-N, abstraction}. That is precisely the
  three-axis `Shape` struct in `shape.rs:93-97`. So `shape.rs` is a faithful
  implementation of a *classification* goal, and the reason it does not answer
  today's question is that the goal was classification, not identity. §5 builds
  on this rather than discarding it.
* `docs/shape_object_perception_grounding.md` — part-based perception for the
  handwriting wall; confirms the shape-math Terms as held. Not otherwise on point.
* `runners/dsl/src/shape_decode.rs` (internal, 7,847 lines) vs this tree's
  (8,093 lines) and `shape.rs` (1,184 vs this tree's copy) — same files, this
  tree's grown by roughly 250 lines. I did not diff them line by line; the module
  docs are identical in the parts I compared. `[unverified]` beyond that.

---

## 5. Part 3, question 1 — what IS a rule's shape, precisely?

**Proposal: a rule's shape is its position in the subsumption lattice over its
own reified body, taken separately for its recogniser half and its constructor
half, and represented as exactly the same kind of object the sd loop already
mints — a `ShapeSignature` whose `signature` is a relation-system.**

That sentence carries four commitments. Each needs its own argument.

### 5.1 Why "lattice position", and not a feature vector

`shape.rs`'s three-axis `Shape` is a feature vector; §2.6 argues that is the
wrong object, and it is worth being precise about *why* rather than just
asserting it. A feature vector supports one question: *are these two things in
the same bucket?* A lattice position supports four:

1. **Are these the same?** (identity — the current `rule_content_hash` answer)
2. **Is this an instance of that?** (`Covers` — downward)
3. **What is the common template?** (`AntiUnify` — the meet, upward)
4. **What is the difference?** (`AntiUnifyWitness`'s σ — and, crucially, that σ
   is itself a first-class object that can be *re-applied* via `Substitute`)

Questions 3 and 4 are what "shape math" means, and a feature vector cannot
express them at all: there is no "difference between recursion=direct and
recursion=structural" that you can apply to a third rule. The creator's own
grounding doc (§4.1) makes exactly this contrast against word vectors:

> the vector offset is a **FLAT, first-order difference** — one translation in
> attribute space; it CANNOT carry the relational graph (which roles bind to
> what, preserved vs altered structure, nesting) — exactly what AntiUnify keeps.

`RuleSummary.keywords_text` is that flat vector, in the most degenerate possible
form (the name). `shape.rs`'s `Shape` is that flat vector in a slightly less
degenerate form (three axes). Neither can answer 3 or 4.

### 5.2 Why the *same object* as the sd loop's, and not a bespoke one

CLAUDE.md's standing rule is explicit: before adding a new mechanism, ask which
of the two existing generative primitives the thing actually is — a quantity
that changes (sd loop) or a set of allowed moves (Γ). A rule-shape is
unambiguously the first: a growable held codebook, decoded against, minted into
when a residual will not fit. So the object should be a `ShapeSignature`, the
codebook should be the existing `ShapeSignature` population (partitioned by
`kind`, exactly as `prog_chunk`, `code_write_construction`, ink strokes and
character compositions already partition it), and the loop should be
`sd_decode` → `sd_recognize` → `sd_transform_decode` → `sd_infer_dimension` →
`sd_mint_quantum` unchanged.

The concrete precedent is already in the tree and is a very close fit. A held
program-idiom entry (`seeds/mbpp_train_diet.json`) looks like:

```json
{ "type": "ShapeSignature",
  "attrs": { "kind": "code_write_construction",
             "name": "mck_prog_a…",
             "chunk_rels": [["ckstmt", 0, "ProgAssignVar"],
                            ["ck", 0, "name", "v0"],
                            ["ck", 0, "value.type", "Lit"],
                            ["ck", 0, "value.value", "slot0"], …] } }
```

A rule-shape entry would be the same object with a different `kind` and a
different flattening. The sd-loop rules that consume it are grain-agnostic
already — `sd_recognize` (`seeds/shape_decode_loop.json`) does
`Argmax(NodesOfType("ShapeSignature"), FixedCount(AntiUnify([obs.signature,
sig.signature])))`, which does not know or care what grain it is scoring.

### 5.3 The flattening: path-addressed rows, as a SET

This is where §2.3's finding becomes design. The program-chunk flattening uses
a **positional** index (`["ck", i, path, atom]`, `i` = statement index) and lands
in a `Value::Tuple`, which is why `Covers` demands equal length. For rules I
propose **path-addressed rows in a `FrozenSet`**:

```
("rt", "<path>", "<variant>")          one row per Term node: its variant at its path
("ra", "<path>", "<field>", "<atom>")  one row per scalar field of that node
("re", "<var>", "<edge_type>", "<var>") one row per match edge (alpha-renamed)
```

where `<path>` is the `child.<field>[index]` route from the body root, exactly
the routing `reflect.rs` already encodes as edge types (`reflect.rs:41`
`CHILD_EDGE_PREFIX = "child."`, plus the `index` edge attr at `:113`).

Three properties follow, and they are the whole reason for the choice:

* **Set semantics ⇒ no equal-length requirement.** `covers_value`'s Set arm
  (`term.rs:3730-3736`) is subset, not length-matched. A pattern that fixes 5
  rows covers any instance containing those 5 rows. §2.3's root cause is gone,
  at this grain, **with zero Rust changes** — `Value::FrozenSet` is already
  authorable from a seed via the `__fset__` tagged form (`persist.rs:4`,
  `py.rs:1067-1069`).
* **Occam is carried by `FixedCount`, not by length.** This matters because
  subset semantics alone would let any pattern cover a large enough instance.
  The sd loop already handles this: `sd_recognize` requires
  `Count(obs.residual) == 0`, i.e. *full* coverage, and ranks candidates by
  `FixedCount` (how many leaf positions the pattern *fixes*). Specificity is
  already the ranking metric; nothing new is needed. This is also the exact
  reasoning `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` §2.1 used to prefer
  the narrow rewrite over the prevalent one — strictness is the signal, a lesson
  CLAUDE.md's Omniglot arc records independently ("STRICTNESS IS THE SIGNAL").
* **Alpha-renaming is part of the signature, not a post-hoc canonicalisation.**
  `("re", "?0", "has_mention", "?1")` rather than `("re", "m", "has_mention",
  "mn")`. §3's measurement shows this is worth 25.58× vs 18.56× — i.e. roughly
  **28% of all structural repetition in the tree is invisible to any
  exact-identity scheme purely because of variable naming.** That is the single
  cheapest correctness improvement in the whole design.

### 5.4 The commitment I am least sure of: two shapes per rule, not one

A rule has a recogniser half (`match` + `where`) and a constructor half
(`effects`). My proposal is that these get **separate signatures with separate
codebooks** (`kind: "rule_match"`, `kind: "rule_effect"`), and that a rule
node references both.

Argument for: they are different lattice *directions*. A `where` clause is a
predicate — its natural operations are `Covers` (does this rule apply here?) and
`AntiUnify` (what do these rules jointly test?). An `effects` list is a
constructor — its natural operations are `Substitute` (build this, with these
fillers) and `Unify` (blend two constructions). Filing both under one signature
would force one set of operations onto both halves; §8 argues in detail that
this is where a naive version of this design breaks.

Argument against, which I want to state because it is not weak: §3 shows the
match clause is near-unique per rule (1.83× sharing, 1,178 singletons out of
2,934) while the where clause is heavily repetitive. So a *match* codebook may
be nearly all singletons — a codebook with 1,178 one-member entries is not a
codebook, it is a list. That may mean the right cut is **three** signatures
(`match` / `where` / `effects`) rather than two, with `match` treated as
essentially unique-per-rule structural data and only `where` and `effects`
codebooked. I do not have enough evidence to settle this and I am flagging it as
the design's first genuine open question rather than picking arbitrarily.

Confidence: **high** on 5.1–5.3 (each rests on code I read and measurement I
ran). **Low-to-medium** on 5.4 — this is the part I would most want a measured
probe on before building.

---

## 6. Part 3, question 2 — what "reference layer over nodes" means concretely

Take a real rule. `note_reported_gap`, from `seeds/gap_awareness.json` (the
explicit-gap-report rule described in CLAUDE.md's "THE AGENT FINDS ITS OWN GAPS"
section). Its `where` clause is an `And` of four items, of which two are this
shape:

```json
{"type": "Exists",
 "source": {"type": "Neighbours", "node": {"type": "Var", "name": "m"},
            "edge_type": "has_mention"},
 "var_name": "mn",
 "predicate": {"type": "Exists",
   "source": {"type": "Neighbours", "node": {"type": "Var", "name": "mn"},
              "edge_type": "refers_to"},
   "var_name": "cc",
   "predicate": {"type": "And", "items": [
     {"type": "Eq", "a": {"type": "TypeOf", "node": {"type": "Var", "name": "cc"}},
                    "b": {"type": "Lit", "value": "Concept"}},
     {"type": "In", "member": {"type": "Attr", "node": {"type": "Var", "name": "cc"},
                               "key": "name"},
                    "container": {"type": "Lit", "value": ["cannot","fail","repeat",
                       "gap","limitation","stuck","unable","struggle","weakness",
                       "broken","wrong"]}}]}}}
```

and the other is **byte-identical except for the variable names (`mn2`/`cc2`)
and the literal word-list** (the self-word list instead of the deficiency-word
list). This is a textbook `AntiUnifyWitness` pair: one template, two σ's, and the
σ's differ in exactly one leaf.

### 6.1 What it is today

* One `Rule` node with three attrs: `match` (a `Value::Tuple` of triples),
  `where` (one nested `Value::Dict` ~40 Term nodes deep), `effect` (a
  `Value::Tuple` of effect tuples).
* On every `tick()`, `run_graph_rules_opts` (`graph_rules.rs:445-496`) creates a
  fresh `TermArena`, walks every `Rule` node, and `rule_from_node` re-parses all
  three attrs into ~40 fresh arena slots per rule.
* Nothing in the graph knows this rule reads `has_mention`, mentions `Concept`,
  or contains two near-identical sub-predicates. (`RewriteRule::read_set` /
  `derive_access` (`substrate.rs:2529`) *does* compute an access set — but into
  the Rust struct, not into the graph, and it records edge/attr *keys*, not
  structure.)
* Its `RuleSummary`, if it had one (it would not — it does not write
  `chosen_action`), would describe it as `"note reported gap"`.

### 6.2 What a reference-layer representation would be

```
Rule{ id: "note_reported_gap", seed: "gap_awareness", version: "1.2.0" }
  ├─ match_shape  ──▶ ShapeSignature{ kind:"rule_match",  name:"agent_received_msg" }
  ├─ where_shape  ──▶ ShapeSignature{ kind:"rule_where",  name:"two_mention_concept_probes" }
  ├─ effect_shape ──▶ ShapeSignature{ kind:"rule_effect", name:"mint_selfconcern_and_wire" }
  ├─ binding      ──▶ Binding{ role:"probe_a_words", value:[…deficiency words…] }
  ├─ binding      ──▶ Binding{ role:"probe_b_words", value:[…self words…] }
  └─ binding      ──▶ Binding{ role:"concern_kind",  value:"knowledge" }
```

with the shared structure held **once**, in the codebook:

```
ShapeSignature{ kind:"rule_where", name:"two_mention_concept_probes",
  signature: fset{
    ("rt","",                          "And"),
    ("rt","items[0]",                  "Exists"),
    ("ra","items[0]","var_name",       "?1"),
    ("rt","items[0].source",           "Neighbours"),
    ("ra","items[0].source","edge_type","has_mention"),
    ("rt","items[0].source.node",      "Var"),
    ("ra","items[0].source.node","name","?0"),
    …
    ("rt","items[0].predicate.predicate.items[1].container", "SLOT"),
    ("ra","items[0].predicate.predicate.items[1].container","role","probe_a_words"),
    …
  } }
```

Note the last two rows: **a slot is a row, not an absence.** A `SLOT` variant
with a `role` field is what makes the signature a *template* rather than a
specific tree, and it is what `Substitute`'s σ binds against. This is the
grounding doc's `template · σ` with the σ carried as graph data.

The concrete node and edge types this adds, in full — this is the entire
vocabulary, and it is deliberately small:

| kind | type | attrs | edges |
|---|---|---|---|
| node | `ShapeSignature` (existing) | `kind`, `name`, `signature` (fset), `support` | — |
| node | `Binding` (new) | `role`, `value` | — |
| edge | `match_shape` / `where_shape` / `effect_shape` (new) | — | `Rule` → `ShapeSignature` |
| edge | `binding` (new) | — | `Rule` → `Binding` |

One new node type, four new edge types, zero new Term variants, zero new Rust.
Whether that is genuinely achievable is §10's question; the *vocabulary* is this
small because everything load-bearing is reuse.

### 6.3 What this buys on this one rule, concretely

* **`("ra", …, "edge_type", "has_mention")` is now a matchable row.** "Which of
  my rules read `has_mention`?" becomes an `Exists`/`Covers` query over held
  signatures instead of a hand-written Python tree-walk. §2.5's three bespoke
  provenance minters collapse into one query each.
* **The two near-identical probes become one template + two σ's**, which is
  what they are. The 478-character stopword-list literal that §3 found repeated
  5× across this family becomes one `Binding` referenced 5 times.
* **The rule is now editable *at the shape*.** Today, "add a deficiency word"
  means editing a literal buried in a `Value::Dict` attr; the daemon's
  `_canon_rule_body` refresh machinery (`jabberwock_daemon.py:550`) exists
  entirely to detect that such an edit happened. Under the reference layer it is
  `set_attr` on a `Binding` node — an ordinary graph mutation an ordinary rule
  can perform. **This is the self-repair payoff CLAUDE.md's "THE AGENT FIXES
  ITSELF WHERE IT IS GRAPH-NATIVE" section names**: the boundary of self-repair
  is the boundary of graph-nativity, and today a rule's *body* is on the wrong
  side of it even though the rule's *identity* is on the right side.

### 6.4 The load-bearing constraint: the reference layer must be a VIEW, not the source of truth

This is the design's hardest constraint and I want it stated before §7 rather
than discovered in §10.

`GAMMA_REFLECTION_WIRING_RESULTS.md` §7 already sized the analogous question for
Γ and reached a clear conclusion: making the graph the actual source of truth for
`check_edge` is *"an O(1)→O(graph) regression on the hottest path in the
substrate — a clear NO."* The rule matcher is on an even hotter path. If
`rule_from_node` had to walk a reference layer and re-assemble a body from
codebook + bindings on every tick, this design would be a straightforward
performance disaster.

So: **the compiled `RewriteRule` in `Substrate::rules` stays the executable
form, exactly as it is today.** The reference layer is a *mirror*, in precisely
the sense `grammar_reflect.rs` established for Γ — written at install time, read
by reasoning, never by the matcher. Round-trip content-equality is the gate
(`grammar_reflect::tests::round_trip_content_equal` is the existing precedent),
and the §2.1 finding — that Γ already does this and Rules do not — means the
pattern is proven in this codebase, at this exact scope, with a passing test.

This also means the design does **not** require solving arena hash-consing.
Hash-consing `TermArena::add` would be a separate, larger, and much riskier
change (it changes `TermIdx` identity semantics, which `ShapeCache`
(`substrate.rs:148`) keys on and which `copy_subtree` (`term.rs:2585+`) assumes
are per-arena). I am explicitly excluding it (§11).

Confidence: **high** on 6.1 and 6.4 (both read directly, and 6.4 has a directly
analogous prior verdict in this repo). **Medium** on 6.2 — that is a design
sketch, and the exact row grammar is the sort of thing that gets three revisions
in contact with a real implementation.

---

## 7. Part 3, question 3 — does rule GROWTH become a decode?

The charter's implication is that authoring a rule should become: decode the
candidate against the held codebook of rule-shapes; recognise → reference an
existing shape; residual → mint a new one. **For the recogniser half I think this
is not only correct but already half-built, in a place nobody has connected to
it. For the constructor half it is correct with an important amendment (§8).**

### 7.1 The evidence that it is already half-built: the composer seeds ARE a codebook

There are 19 `composer_*_graph.json` seeds. Each carries one or two `Rule` nodes
whose *effects* mint another Rule by `set_attr`-ing a fully literal
`match`/`where`/`effect` blob. From `seeds/composer_decision_graph.json`:

```json
["add_node",  "rn0", "Rule", {"minted": 0.0}],
["set_attr",  "rn0", "id",    {"__term__": {"type":"StringConcat","parts":[
                                 {"type":"Lit","value":"decide_under_uncertainty_"},
                                 {"type":"Attr","node":{"type":"Var","name":"cr"},"key":"tag"}]}}],
["set_attr",  "rn0", "match", [["game","has_goal","goal"]]],
["set_attr",  "rn0", "where", null],
["set_attr",  "rn0", "effect", [ … a fully literal Argmax-over-affordances tree … ]]
```

**That is a template plus one slot (`tag`), hand-written, one file per shape.**
It is a codebook whose entries are executable emitters rather than data, whose
"decode" is a `ComposerCue` priority table (`seeds/composer_dispatch.json`),
and whose "mint" is a human writing a twentieth JSON file. §3 measures the
family at 4.16× internal structural repetition.

Under the design: 19 files of emitters become 19 `ShapeSignature{kind:
"rule_effect"}` entries plus **one** generic instantiation rule whose effect is
`Substitute(template, sigma)`. The `_compose_*_rule` Python builders
(`reflective_faculty.py:1780, 1925, 1974, 2124, 2165, 2211, 2257, 2450, 2486,
3646, 4050, 5083` — twelve of them) are the Python mirror of the same table and
collapse the same way.

That is the strongest concrete argument in this whole document that the design
is *right*, as opposed to merely *coherent*: the codebook already exists, it is
just written as 19 programs instead of 19 data rows, and the thing that makes it
19 programs is exactly the absence of `Substitute` on an addressable body.

### 7.2 What the growth loop looks like

Unchanged sd-loop rules, new `kind`:

1. **`sd_decode`** — a candidate rule body's signature is decoded against
   `ShapeSignature{kind:"rule_where"}` entries. Residual = unmatched rows.
2. **`sd_recognize`** — residual empty ⇒ the candidate *is* a held shape;
   reference it, mint bindings for the σ, no codebook growth.
3. **`sd_transform_decode`** — residual is one uniform delta in one dimension ⇒
   a `Transform`. For rules this is a genuinely natural fit and it subsumes work
   that is currently bespoke: `ShiftThresholdLits` (§2.6) is *precisely*
   `Transform{dim: "threshold_literal", delta: k}` applied to a held shape;
   `apply_flip_comparison` is `Transform{dim: "comparison_direction",
   delta: 1}` in the modular-2 base the `modular` `DimensionGenerator` already
   provides (CLAUDE.md, BASE-AS-DIMENSION). Both currently exist as one-off
   appliers with their own Rust Term and Python function respectively.
4. **`sd_infer_dimension`** — a residual coupled across observed dims mints a
   `LatentDimension`. `[unverified]` whether this rung ever fires usefully at
   rule grain; I would expect it to be the last rung to earn its place and I am
   not claiming it will.
5. **`sd_mint_quantum`** — only after 2–4 fail. Genuinely novel rule shape ⇒ a
   new codebook entry, `codebook_epoch` bumps, `sd_redecode` re-arms.

The whole thing runs in one `run_rules` fixpoint, exactly as CLAUDE.md's
dynamic-quantization section describes, with no Python iteration.

### 7.3 What this changes about the current authoring path

Today: `ground_concern` → a `ComposerCue` priority `Argmin` → a name-keyed
registry lookup → one of twelve `_compose_*_rule` builders → a JSON blob →
`add_rule`. The *choice* is graph-native (the cue table is data); the
*construction* is twelve Python functions.

Under the design: the choice becomes a `ShapeDecode` over the rule-shape
codebook (the same Term that already does composer dispatch — CLAUDE.md:
*"`compose_design_for_goal` and `induce_concern` are the SAME op at two points
of one loop"*), and the construction becomes `Substitute`. The twelve builders
become twelve data rows. **The registry-lookup seam that CLAUDE.md currently
defends as "mechanical, not a decision" stops needing defending, because there is
nothing left to look up.**

Confidence: **medium-high**. 7.1 is measurement plus direct reading of the seed
files and is solid. 7.2 is design; the transform rung's fit is argued and I
believe it, but it is not demonstrated. 7.3's collapse is a claim about twelve
Python functions I read the signatures of, not the bodies of — some of them
(`_compose_experiment_rule`, at 400+ lines with a documented 15-leaf
`IfThenElse` structure in its graph twin) will not collapse as cleanly as the
sentence implies.

---

## 8. Where the analogy breaks: `effects` resists decode, and the fix is not to force it

The brief asked me to be honest about whether some part of a rule resists the
decode framing. **Yes. `effects`.** Three distinct problems, in increasing order
of how much they matter.

### 8.1 Effects are a construction, not a recognition — but this is a feature

Superficially this looks fatal: the sd loop is a *recogniser*, and effects are
not the kind of thing you recognise. But the creator's own grounding doc
(§4.1) already answers this and the answer is the lattice's other direction:

> **"X but with Y" = move DOWN the lattice (instantiate via SUBSTITUTE),
> "abstract X out / vice versa" = move UP (anti-unify).**

An effects list *is* recognisable — you can `AntiUnify` two effect lists and get
a template — but the operation you want at *use* time is `Substitute`, not
`Covers`. So the effect codebook is a real codebook whose entries are consumed
downward. That is why §5.4 proposes separate signatures: same lattice, opposite
direction of travel, and one `kind` cannot express "this entry is for
recognising" and "this entry is for building" simultaneously without the
consumer guessing.

This is not a break. I list it first because it *looks* like one and I want it
disposed of explicitly.

### 8.2 The real break: effects have an ORDER, and order is not a set

§5.3's whole argument for `FrozenSet` rows rests on subset semantics being the
right matching relation. **For effects it is not.** These two effect lists are
not interchangeable:

```
[["add_node","n","Concern",{…}], ["add_edge","agent","has_concern","n"]]
[["add_edge","agent","has_concern","n"], ["add_node","n","Concern",{…}]]
```

The second binds `n` before it exists. Effect application is sequential and
variable-binding is order-dependent (`Effect::AddNode { new_var, … }` binds
`new_var` for subsequent effects — `graph_rules.rs:248-260`).

Under a set-of-path-addressed-rows encoding, order *is* preserved — the path
`effects[0]` vs `effects[1]` is part of every row — but then subset matching
becomes position-sensitive again and §5.3's advantage evaporates for this half.
Two effect lists that do the same thing in a different order will not match.

**I do not think this should be papered over, and specifically I think the
tempting fix is wrong.** The tempting fix is a canonical topological ordering of
effects before signature construction. That is exactly the "canonicalize before
hash" mechanism `PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` §3 considered
and correctly declined as the larger, riskier of two options — and it has the
additional problem that effects are *not* in general reorderable (`del_node`
followed by `add_edge` is not the same as the reverse), so a canonical order
would have to be semantics-aware, which is a def-use analysis this project
explicitly does not have (that results doc, §1: *"No live-variable / def-use
analysis Term exists in the Rust engine today"*).

**My recommendation: accept it. Effect signatures stay position-addressed and
match strictly.** Two effect lists match iff they are the same construction in
the same order. This is a real loss of recall and it is the honest price. It is
also, per the Omniglot arc's own standing finding, probably the right side to err
on ("STRICTNESS IS THE SIGNAL"; every partial-credit relaxation in that arc lost).

### 8.3 The subtler break: an effect's `attrs` dict carries `{"__term__": …}` computed args

`parse_effect_arg` (`graph_rules.rs:157-176`) treats an effect argument as either
a literal `Value` or, if it is a dict with a `__term__` key, a computed Term. So
an effects list is a *tree containing arbitrary sub-Terms*, and those sub-Terms
are exactly the kind of thing the recogniser codebook should hold — see
`sd_recognize`'s own `covered_by` effect, which embeds a four-level
`Argmax(NodesOfType, FixedCount(AntiUnify(…)))` tree inside a `set_attr`.

So the clean two-way split of §5.4 is not quite clean: an effects signature
contains recogniser-shaped subtrees. This is not fatal — the path-addressed
encoding handles nesting fine, and a computed arg's subtree can carry its own
reference into the `rule_where`-kind codebook (that is what makes it a *reference
layer* rather than a flat table). But it means the two codebooks are not
independent, and a design that assumed they were would discover this the hard
way. Naming it here so it is discovered cheaply.

Confidence: **high** on 8.2's mechanism (read `graph_rules.rs`'s effect parser
and binding semantics). **Medium** on the recommendation — "accept strictness" is
a judgement call informed by the Omniglot arc's measured record, not a proof.

---

## 9. Part 3, question 4 — what does this buy that the current design cannot do?

### 9.1 The dead-temp example, walked through precisely

The brief asked whether, under a reference-layer design, `t = a + b; return t`
would become recognisable as equivalent to `return a + b`, and specifically
whether it requires the transform `dead_temp_elim` to be a minted, referenceable
`Transform` object such that both forms reference the same underlying
computation-shape via different deltas.

**Working it through: yes, and yes — with an important boundary.** Three things
have to be true, and only two of them are about shape.

**Step 1 — the length trap dissolves, and this part is genuinely free.** Under
positional `chunk_rels`, the two forms have 10 rows and ~5 rows respectively;
`covers_value`'s Tuple arm (`term.rs:3727`) rejects them before looking at
content. Under path-addressed rows in a `FrozenSet`, the reduced form's rows are
*not* a subset of the original's either — the paths differ (`stmts[0].value.*`
vs `stmts[0].*`) — so set semantics alone does **not** make them match. §2.3's
finding removes the *spurious* barrier (length), not the *real* one (the two
trees genuinely have different structure). I want to be exact about this because
it would be easy to overclaim: **path-addressed sets are necessary and not
sufficient.**

**Step 2 — the transform has to exist as an object.** This is the brief's own
hypothesis and I think it is exactly right. `dead_temp_elim` is a rewrite:
`Assign(X, E) ; Return(Var X)` ⟶ `Return(E)`. Under the design it is a
`Transform{dim: "dead_temp", delta: 1}` in the codebook, and the two forms are
the *same* held shape at `delta: 0` and `delta: 1` respectively. `sd_transform_
decode` then recognises the second as the first-plus-a-delta, at rung 2, without
minting — which is precisely CLAUDE.md's "Transformation = quantum change in a
specific dimension", applied at a new grain.

**Step 3 — and this is the boundary — the transform's *validity* is not a shape
question.** Whether `dead_temp_elim` is *sound* rests on the argument
`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md` §2.1 makes: `ProgReturn`
terminates control flow, so nothing can observe `X` afterward, and `E` is
evaluated exactly once at the same point in both forms. That is a semantic proof
about an evaluation model. **No amount of shape math produces it.** A
reference-layer design makes the transform *representable, referenceable, and
composable* once someone has proved it sound; it does not prove it.

This matters for how the design should be sold. The honest claim is: *under a
reference layer, a proved-sound rewrite becomes a first-class object that the
recogniser can then use everywhere, instead of a special case someone has to
build a mechanism for.* The dishonest claim would be that shape math discovers
equivalences. It does not.

**And the NO-GO stands regardless.** That rung measured 0/40 corpus payoff and
0/15 against the held codebook. A better mechanism for recognising something that
occurs zero times is still worth zero. If this design is built, it should not be
justified by the chunk-equivalence case; that case is a good *illustration* of
the root cause (§2.4) and a bad *business case*.

### 9.2 What it buys that is not hypothetical

Ranked by how confident I am:

1. **The three bespoke provenance minters collapse into queries** (§2.5). This is
   the clearest win: `_ensure_acting_rule_provenance` /
   `_ensure_reply_rule_provenance` / `_ensure_where_literal_rule_provenance` are
   three ~80-line Python functions that exist to answer three structural
   questions about rules; each becomes an `Exists` over held signature rows. A
   *fourth* question needs no fourth function. **Confidence: high.**
2. **Rule selection gets a FAC stage** (§4.2). `_pick_acting_rule`'s
   name-keyword `Argmax` becomes: cheap keyword filter (MAC, keep it) → escalate
   survivors to `StructSim`/`Covers` over held signatures (FAC). This is exactly
   the fix the creator's own grounding doc prescribes, applied to the layer that
   still has the disease. **Confidence: high** that the defect is real; **medium**
   that the fix improves any measurable outcome, because I have no measurement of
   how often `_pick_acting_rule` currently picks wrong.
3. **Rule authoring becomes data** (§7.1): 19 composer seeds + 12 Python builders
   → ~31 codebook rows + one `Substitute` rule. **Confidence: medium-high**, with
   the §7.3 caveat that the largest builders will not collapse cleanly.
4. **Six Rust Terms stop needing to exist** (§2.6) — as *new* work; the existing
   ones stay for compatibility. The real claim is that the *next* structural
   question needs no seventh. **Confidence: medium.**
5. **Structural sharing**: 3.2× on cognition seeds, 25.6× on embodied seeds
   (§3). **Confidence: high on the numbers, low on their importance** — this is
   the weakest of the five and I have deliberately ranked it last, against the
   temptation to lead with the biggest number in the document.

### 9.3 Does this change the Γ / admissibility side?

The brief asked whether Productions are a rule-shape special case or a different
shape family. **My answer: a different family, and the difference is
directional, not structural.**

Structurally they are close: a `Production{src-pattern, edge_type, tgt-pattern,
where, weight}` (`grammar.rs`) has a where-clause Term and a weight Term, both of
which already reflect into `Term.*` subgraphs (§2.1). So the *encoding* work is
already done for Γ and not done for Rules — the exact inverse of what the brief
assumed. Adding a signature to a `GammaProduction` is strictly easier than adding
one to a `Rule`, because `production_from_node` already gives you an addressable
body.

Directionally they differ in the way CLAUDE.md's SHAPES-NOT-NUMBERS section
already names: Γ **generates** a set of admissible moves; a Rule **fires** on a
match. A Production's natural shape question is *"what does this generate?"* —
which is `Substitute`-shaped (constructor), like effects, not `Covers`-shaped.
So if the two-codebook split of §5.4 is right, a Production's signature belongs
in the *constructor* family with `rule_effect`, not the recogniser family with
`rule_where`.

There is a second-order observation here that I think is more interesting than
the first-order answer, and I offer it as an observation rather than a proposal
because I have not worked it through: `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` finds
15 violence rules across 4 seeds, **none of which declares a single Γ
production**, and argues they *should* be a generated absence. If Rules and
Productions shared one constructor-side codebook, "this family of 15 rules is
really one production" would become a *decodable* claim — the 15 rules would
decode to one shape with 15 σ's, which is what "they should be one production"
means, stated in the algebra. **`[unverified]`** — I did not read those 15 rules,
and I am not claiming they would in fact decode that way. I am noting that the
design would make the question askable, which it currently is not.

---

## 10. Part 3, question 5 — what would this cost, honestly?

Building is out of scope. Sizing is not, and the project's culture is to size in
real files with real regression surface.

### 10.1 Order of magnitude

**This is a self-contained subsystem addition with one foundational-shaped
risk.** Not a foundational rewrite — and the reason is §6.4: the executable path
(`RewriteRule` in `Substrate::rules`, `rule_from_node`, `run_rules`) is
*untouched*. Everything proposed is a mirror written at install time and read by
reasoning. That is the same shape, and the same risk profile, as the Γ reflection
wiring rung, which landed in ~300 net new lines of Rust
(`GAMMA_REFLECTION_WIRING_RESULTS.md` §1).

The comparison is close enough to be useful and I want to be clear where it
breaks: that rung mirrored `add_production`, whose Rust-inherent caller count is
**two**. `add_rule`'s caller count is very much larger, and the graph-`Rule`-node
population is larger still (2,934 rules across 634 seed files, §3). So: same
architectural shape, materially larger blast radius.

### 10.2 The files, and what happens to each

| file | change | size |
|---|---|---|
| `runners/dsl/src/rule_reflect.rs` (new) | the exact analogue of `grammar_reflect.rs`: `rule_to_subgraph` / `rule_from_subgraph` / signature construction | ~350–450 lines incl. tests |
| `runners/dsl/src/substrate.rs` | wire the mirror into `add_rule`; a `rule_graph_root`; accessor | ~40 lines + the §10.4 fallout |
| `runners/dsl/src/graph_rules.rs` | mirror on the graph-`Rule`-node install path too, or explicitly not (a scope decision) | 0–40 lines |
| `runners/dsl/src/term.rs` | **probably zero.** See §10.3 | 0 |
| `runners/dsl/src/reflect.rs` | unchanged (the generic mechanism is already right) | 0 |
| `seeds/rule_shape_loop.json` (new) | the `kind`-scoped sd-loop instantiation + the generic `Substitute` authoring rule | ~200–400 lines JSON |
| `domains/reflective_faculty.py` | the 12 `_compose_*_rule` builders become data; 3 provenance minters become queries | **−1,500 to −2,500 lines**, eventually |
| `domains/edit_ops.py`, `domains/self_correction.py`, `domains/self_model.py` | the hand-written tree-walkers become queries | −200 to −400 lines |
| `seeds/composer_*_graph.json` (×19) | become codebook rows | net reduction |

The Python column is the interesting one: on the numbers above, **this design is
net line-count negative** if it is carried through, and the deletions are exactly
the class of Python that CLAUDE.md's architecture rule most wants gone (structural
decision logic over graph state, currently living in Python because there is no
graph object to put it on). That is a strong argument for the design and a
terrible argument for doing it all at once (§11).

### 10.3 Does it need new Rust Terms? Probably not — check this first

§4.1's finding is what makes this answerable: `AntiUnifyWitness` (the σ),
`Substitute` (apply σ), `Unify` (blend), `StructSim` (graded compare) all exist.
`Covers` exists with the set semantics §5.3 needs. `FrozenSet` is authorable from
a seed (`__fset__`). `ShapeDecode` / `sd_*` are grain-agnostic.

The one genuine gap is `Covers`-with-witness (grounding-doc item 3, §4.1). Whether
it is needed depends on whether recognising a rule against a codebook entry must
also *return* the bindings, or whether `AntiUnifyWitness` over the pair suffices
(it computes both template and σ's, so it may). **I do not know, and this is the
first thing I would check before writing any Rust** — because "zero new Term
variants" versus "one new Term variant" is the difference between a wiring rung
and a language-extension rung, and the whole cost estimate above assumes the
former.

### 10.4 The single riskiest / most uncertain part

**Not the shape math. The node-ID and install-order fallout from making
`add_rule` allocate graph nodes.**

`GAMMA_REFLECTION_WIRING_RESULTS.md` §5 found this the hard way, at the
*smallest possible scale*: mirroring `add_production` allocated 5 graph nodes per
call, which shifted every subsequently-inserted `NodeID` by 5 and broke a Rust
unit test that hard-coded `NodeID(3)`. That rung then flagged, unfixed, the
larger version of the same risk: *"129 real call sites across `tests/*.py`, 18 of
which were found (grep) to combine `add_production(` with node-count-shaped
assertions in the same file — exactly the class of regression §5 found and fixed
in the Rust suite, but at Python-test scale where the fix-cost per broken test is
unknown without actually running them."*

For `add_rule` the equivalent number is much larger and I did not measure it.
A rule's mirror is not 5 nodes — a 40-node where-clause is ~40 `Term.*` nodes plus
edges, and §3's 925,002 Term nodes across the seed corpus is the upper bound on
what full mirroring would add to a fully-loaded graph. Any test that counts
nodes, any test that asserts a `NodeID`, any checkpoint size assumption, any
`graph_to_dict` round-trip that enumerates types — all are in the blast radius.

**Secondary risk, and it is not small: `persist`/checkpoint size and boot time.**
The daemon resumes from checkpoints and already has a rule-refresh mechanism
(`_reconcile_seed_rules`, `_REFRESHABLE_SEEDS`) that CLAUDE.md records as having
silently run stale rule bodies until it was fixed. Adding a large mirror
population to what gets serialised, and a *second* representation that can drift
from the first, is exactly the shape of bug that took ten days to notice last
time.

**Mitigation that I think actually works, and is the reason I would not call this
foundational:** mirror **lazily and selectively**, not on every `add_rule`. A
rule's signature is only needed when something asks a shape question about it.
`ShapeCache` (`substrate.rs:148`) is the existing precedent for exactly this
pattern at Term grain. A `mirror_rule(idx)` called on demand, plus a codebook
built once at boot for the seeds that opt in, has a fraction of the blast radius
of unconditional mirroring — at the cost of the reference layer being incomplete
at any given moment, which for a *reasoning* mirror is acceptable in a way it
would not be for an executable one.

Confidence: **high** that this is the riskiest part (it is the one with a
documented prior incident at smaller scale). **Medium** on the mitigation —
lazy mirroring is a real pattern in this codebase but I have not checked whether
anything in the reasoning path would need the mirror to be complete.

---

## 11. Part 3, question 6 — what should stay OUT, and the smallest slice that tests the hypothesis

### 11.1 Explicitly out of scope

1. **Hash-consing `TermArena`.** §6.4. It changes `TermIdx` identity semantics,
   which `ShapeCache` keys on and `copy_subtree` assumes. It is a separate
   project with its own correctness surface and it is not needed for anything
   here.
2. **Making the reference layer the source of truth for matching.** §6.4. The
   Γ rung already reached this verdict for `check_edge` and the rule matcher is
   hotter. If this is ever revisited it needs its own prereg.
3. **Canonical reordering of `effects`.** §8.2. It needs a def-use analysis this
   project does not have, and the analogous "canonicalize before hash" mechanism
   was already declined once on smaller grounds.
4. **Retrofitting the 2,934 existing seed rules.** A design that requires
   rewriting every seed is a design that will not land. The reference layer must
   be *derivable* from an existing rule (that is what `rule_to_subgraph` is), so
   existing seeds need zero edits; only new authoring uses the codebook.
5. **Unifying Rules and Γ Productions into one object.** §9.3 argues they are
   different families. Even if they converge, that is a later question and
   bundling it here would double the blast radius for no test-of-hypothesis
   value.
6. **Any claim that this improves a benchmark.** Per CLAUDE.md's standing rule
   ("synthetic-proven mechanism ≠ benchmark value, report both"), the mechanism
   claims in §9.2 are mechanism claims. I have no measurement that any of them
   move any number, and §9.2 item 2 in particular I flagged as unmeasured.

### 11.2 The smallest slice that would actually test the hypothesis

The core hypothesis is: **rule-shape recognition, done structurally, picks
better rules than name-keyword overlap does.** Everything else in this document
is downstream of that being true.

The slice that tests it, and nothing else:

* **Build only** `rule_signature(rule) -> FrozenSet<row>` — the flattening of
  §5.3, path-addressed, alpha-renamed, over `where` only (not `match`, not
  `effects` — §5.4's uncertainty and §8's breaks are both avoided). This is a
  pure function of an already-parsed `RewriteRule`; it writes no graph nodes,
  allocates no NodeIDs, and therefore has **none** of §10.4's risk.
* **Store it** as one attr on the existing `RuleSummary` nodes — the population
  already exists, already gets minted, already gets queried. No new node types,
  no new edges, no mirror, no lifecycle.
* **Measure one thing**: on the existing `_pick_acting_rule` call sites, compare
  the name-keyword `Argmax` against a `StructSim`/`FixedCount` rank over the new
  signatures. The concern residuals that drive it are already captured in the
  self-improvement path's own test fixtures.

That is a few hundred lines, entirely additive, zero regression surface on the
matcher, and it produces the one number nobody has: **does structural rule
selection differ from name selection, and when it differs, is it better?**

Two honest notes on this slice. First, per the run-15 correction in CLAUDE.md,
this measurement has to be *powered* before it is believed — a difference on
five concerns is not a result. Second, and more awkwardly: I do not currently
know what the ground truth is. "Better rule pick" needs an oracle, and the only
oracle available is the downstream experiment verdict (does the variant get
adopted?), which is slow and noisy. **Designing that measurement is genuinely
harder than building the slice**, and if I were writing the prereg for this I
would spend most of it there rather than on the mechanism.

If that slice shows nothing, the whole design is still *coherent* — the
line-count and self-repair arguments in §9.2 and §6.3 survive — but it is no
longer *urgent*, and it should not be built at the scale of §10.

---

## 12. What this document does NOT establish

Stated plainly, in the order a reviewer is most likely to need them.

1. **It does not establish that any of this improves any measured outcome.**
   §9.2 ranks five benefits by my confidence in the *mechanism*; not one of them
   has a number attached. §11.2 exists because that gap is real.
2. **It does not establish that the two-codebook split (§5.4) is the right cut.**
   §3's match-clause measurement (1.83×, 1,178 singletons) actively suggests a
   three-way split might be better. I did not resolve this.
3. **It does not establish that `Covers`-with-witness is unnecessary** (§10.3).
   The whole "zero new Rust Terms" cost claim hangs on that and I did not check
   it.
4. **It does not establish that the shape-math Terms are unused by the rule
   layer** — only that I grepped and did not find a caller (§4.1). A seed I did
   not open could be using them.
5. **It does not measure the live graph.** §3 is a scan of *seed manifests*. A
   booted agent's actual rule population, and what its bodies expand to in the
   live graph, may differ — some seeds are not loaded by default, and the
   per-tick arena means the runtime cost profile is not the same as the storage
   profile. I did not boot an agent.
6. **It does not size §10.4's blast radius.** I identified it as the riskiest
   part by analogy to a documented prior incident; I did not run the grep that
   would count node-count-shaped assertions in `tests/` the way
   `GAMMA_REFLECTION_WIRING_RESULTS.md` §7 did for `add_production`. That grep is
   the first thing a prereg for this should contain.
7. **It does not include the agent's own view.** §4.4 is an honest null: the
   capture harness exists, the concern it frames is on-point, and no output
   survives that I could find. Every design judgement in Part 3 is mine, and the
   creator's methodology in the research repo is explicitly that *the agent*
   should design from grounding. This document does not honour that methodology;
   it substitutes for it. Re-running `jabberwock_designs_rule_index.py` against a
   current agent, with the §5.3 flattening framed as the concern, would be a
   cheap and more faithful next step than anything in §11.
8. **It does not re-verify the citations in the creator's grounding docs.** I
   quoted `shape_math_grounding.md` and `order_n_shape_matching_grounding.md`
   as fetched text and checked their claims about *this codebase* (which held,
   strikingly). I did not check Plotkin 1970, Cerna & Kutsia 2023, Ontañón &
   Plaza 2010, or the SME/MAC-FAC literature against primary sources.
   `[unverified]` for all bibliography.

---

## 13. Reproduce

Every number in §3:

```bash
cd /home/matt/ozmadev/ocelot
# The scan script is in this session's scratchpad, not committed:
#   .../scratchpad/rule_share_scan.py
# It reads only seeds/*.json and mutates nothing. In summary it:
#   1. loads every seeds/*.json, takes entries under "rules" that have
#      BOTH "match" and "effects" (2934 of 4107; the other 1173 are
#      microtheory entries keyed head/body or if/then/why);
#   2. walks every Term-JSON node in "where" plus every {"__term__": ...}
#      computed effect argument;
#   3. buckets each subtree under three canonicalisations:
#      exact / alpha (Vars renamed positionally) / alpha+lit (Lits wildcarded).
```

Code claims, in this tree at `9b775cf`:

```bash
sed -n '2222,2226p'   runners/dsl/src/term.rs         # TermArena::add — pure append
sed -n '3711,3739p'   runners/dsl/src/term.rs         # covers_value — Tuple len check vs Set subset
sed -n '824,872p'     runners/dsl/src/term.rs         # AntiUnifyWitness / Substitute / Unify / StructSim
sed -n '178,275p'     runners/dsl/src/term.rs         # ShiftThresholdLits / RewriteTreeNodes / AttrKeyRanking
sed -n '45,121p'      runners/dsl/src/reflect.rs      # term_to_subgraph — unconditional insert_node
sed -n '362,428p'     runners/dsl/src/graph_rules.rs  # rule_from_node — reads attrs, not subgraphs
sed -n '2480,2560p'   runners/dsl/src/substrate.rs    # add_rule — no graph write
sed -n '2229,2247p'   runners/dsl/src/substrate.rs    # rule_content_hash — all-or-nothing FNV
sed -n '2615,2765p'   domains/reflective_faculty.py   # RuleSummary mint + _pick_acting_rule
sed -n '49,145p'      domains/edit_ops.py             # the hand-written structural walkers
sed -n '50,97p'       runners/dsl/src/shape.rs        # the three-axis Shape struct
grep -rn "term_to_subgraph\|term_from_subgraph" runners/dsl/src/*.rs   # four real callers
```

Creator's prior work (private repo, raw fetch):

```bash
gh api -H "Accept: application/vnd.github.raw" \
  repos/ozmalabs/internal/contents/research/experiments/gamma-substrate/docs/shape_math_grounding.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/ozmalabs/internal/contents/research/experiments/gamma-substrate/docs/order_n_shape_matching_grounding.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/ozmalabs/internal/contents/research/experiments/gamma-substrate/scripts/jabberwock_designs_rule_index.py
gh api repos/ozmalabs/internal/contents/research/experiments/gamma-substrate/results --paginate --jq '.[].name' | grep -i "rule\|index"
```

---

## 14. The answer, in one paragraph

**Yes, qualified.** Rules should be a reference layer over nodes, and the
sharpest reason is not compression and not elegance — it is that the agent
currently selects which of its own rules to modify by counting substring matches
against the rule's *name* (`RuleSummary.keywords_text = name.replace("_", " ")`,
`reflective_faculty.py:2691`), while every genuinely structural question about a
rule body is answered by a hand-written Python tree-walker or a purpose-built
Rust Term. That is precisely the "MAC stage treated as the verdict, with no FAC
stage" defect the creator diagnosed for concept-analogy in June 2026, sitting
undetected in the self-improvement path. The algebra to fix it was researched in
the same month and then **built** — `AntiUnifyWitness`, `Substitute`, `Unify`,
`StructSim` are in `term.rs` today — so what is missing is not shape math but an
addressable object for it to operate on. The qualification is that a rule's two
halves want opposite directions of the same lattice: `match`/`where` is a
recogniser (`Covers`, upward via `AntiUnify`) and `effects` is a constructor
(`Substitute`, downward), and `effects` additionally carries an order that
genuinely resists set-semantics matching — so the honest design gives them
separate codebooks, accepts strict order-sensitive matching on the effects side,
and keeps the whole reference layer a *mirror* that the hot matcher never reads.
