# Should the MBPP op-list gate ladder become a Γ production? — RESULTS

Prereg: `OPLIST_ADMISSIBILITY_GRAMMAR_PREREG.md`, same worktree/branch. Base
`main @ c5aea7b` ("Record retelling-decay build landed (ozmalabs/bigville
acf0961)"), verified via `git log --oneline -1 main` immediately before
creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/oplist-admissibility-grammar`, branch
`oplist-admissibility-grammar` — **not merged to `main`**, left for the
orchestrator to review and merge, per this session's explicit instruction. **A
sibling agent is concurrently building `GroupCount`/`DictMerge` in
`runners/dsl/src/synth_enumerate.rs` and adjacent `domains/prog_synthesis.py`
territory; this task touches neither file.** `git diff --stat c5aea7b` is
empty for every source file — confirmed at the end of this document (§9).

**Headline: GO on the design, NOT-YET-READY to build without one more priced
decision.** The op-list boolean ladder genuinely IS Γ-shaped — a real
generated multi-production admissible-move SET, not a single-classification
recognize problem, which is the correct discriminator per CLAUDE.md's own
"quantity that changes vs. set of allowed moves" test. Unlike `SHAPE_AUDIT.md`'s
159/634-seed finding, this design does **not** need any new Rust
admissibility-checking machinery — `is_edge_admissible`/`admissible_edges_from`
are already PyO3-exposed and already call `ConsistencyChecker::check_edge`
(`py.rs:7922-7956`) — so a correctly-built version of this would be **properly
enforced**, not decorative Γ. What is genuinely missing, and is real
engineering rather than a reshuffle: (1) two new graph node types with no
seed-side precedent today (`SynthSpecShape`, `SynthOp`), (2) a decision on
whether the evidence-flag computation is duplicated in Python (cheap, drift-
risky — the exact class of risk `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
REASSESSMENT_PREREG.md`'s own Q1 flags for `NATIVE_ORACLES`) or newly exposed
from the Rust computation that already exists (clean, needs a small Rust
change this task is not permitted to make), and (3) a MINT mechanism whose
per-candidate cost is a full enumerator search plus a held-out-row check —
genuinely more expensive than the sd loop's cheap in-tick pattern-match mint,
and honestly not tick-time machinery but an offline sweep. The buildable first
slice (§8) is scoped to avoid deciding (2) blind.

---

## 1. The real gate population, read in full

`eval_synth_enumerate` (`runners/dsl/src/synth_enumerate.rs:1666-2036`,
read in full) computes evidence flags directly from the spec's own `Value`
rows (never from NL prose — that is a different, already-separately-scoped
mechanism, §1.4 below) and uses them to build `default_ops`, consulted only
when the caller passes no explicit `ops` (`ops_t` evaluates to `Value::None`,
line 2028). Every flag and every gate it feeds, in the order they appear:

| evidence flag (definition line) | what it tests | op(s)/template(s) it admits, and the gate site |
|---|---|---|
| `spec_is_string_shaped` (1763) | every var + output is `Str`/`Surface(Text)` | selects `DEFAULT_STR_OPS` wholesale (1893-1898) — a typed-default SWITCH, not an incremental gate |
| `spec_is_list_shaped` (1774) | output all list-like, OR some var consistently list-like across rows | selects the `DEFAULT_OPS ∪ LIST_EXTRA_OPS` branch (1914) vs. the plain-`DEFAULT_OPS` fallback (2019-2022) |
| `spec_output_is_listlike` (1789) | output all `Tuple`/`List`/`Set`/`FrozenSet` | gates `TUPLE_BUILD_OPS` (1917-1919), `Sort` (1926-1928), and (jointly with `spec_has_string_value`) `Split` (1938-1940) |
| `spec_output_is_setlike` (1792) | output all `Set`/`FrozenSet` | switches to the dedicated `SET_DEFAULT_OPS` bucket (1899-1913) instead of the list-shaped branch |
| `spec_has_string_value` (1802) | any row var or output is string-shaped | admits `Replace,Split,StrCount,Capitalize,Str,ParseInt` via `extra_evidence_ops` on the plain-`DEFAULT_OPS` branch (1884-1885); jointly gates `Split` (1938) and `ParseInt`'s exclusion (1976) on the list-shaped branch |
| `spec_has_float_value` (1805) | any row var or output is `Float`/`Rational` | admits `Round` (1887-1889, 1956-1958); jointly excludes `ParseInt` (1977) |
| `spec_has_dict_value` (1817) | any row var is `Dict` | admits `DictItems,SortBy,Reverse` (1993-1997) — the original, narrower `SortBy` gate (task 475) |
| `spec_has_repeated_list_element` (1846) | any row var/output has a duplicate element | admits `IndexedMap` (1890-1892 on the plain branch, 1981-1983 on the list-shaped branch) |
| `spec_has_list_of_lists` (1856) | a list-shaped var/output whose OWN elements are all list-like | admits `SortBy` a SECOND way (2015-2017, the exact CEILING_REASSESSMENT_3 fix) — deliberately NOT re-widening `DictItems`/`Reverse` |
| `spec_has_string_list_elements` (1870) | nested: a list var/output whose elements are all string-shaped | template-pool-only, never `op_list` — see §1.2 |
| `spec_has_float_list_elements` (1878) | nested: a list var/output with any float element | template-pool-only, never `op_list` — see §1.2 |
| `spec_output_is_bare_int` (1972, inline) | output all `Int` | jointly admits `ParseInt` on the list-shaped branch (1974-1979) |

**Eleven top-level evidence flags, feeding at least fourteen distinct
`v.push(...)`/branch-selection sites.** All fourteen are read directly above,
not summarized from a prior document.

### 1.2 A second population one level down: per-element TEMPLATE gates

`map_templates_by_size`/`indexed_map_templates_by_size` construction
(`synth_enumerate.rs:2460-2585`, read in full) is the **same evidence-gate
shape**, one grain finer — it does not decide which `op_list` NAME is
admitted, it decides which per-element BODY template an already-admitted
`MapList`/`SortBy`/`SetMap`/`IndexedMap` may compose over:

- `sorted(item)` — `set_map_wanted || spec_has_list_of_lists` (2480)
- `reverse(item)` — `spec_has_string_value || spec_has_string_list_elements` (2502)
- `capitalize(item)` — same disjunct (2509)
- `str(item)` — unconditional once inside the `map_wanted` block (2521, no
  further gate — a deliberate exception, commented as such: "no further
  narrowing is needed")
- `round(item, c)` — `spec_has_float_value || spec_has_float_list_elements` (2529)
- the `IndexedMap` template pool (2543-2585) is gated wholesale on
  `indexed_map_wanted` (a derived flag: `IndexedMap` present in `op_list`,
  line 2195) — internally unconditional once inside.

**This document treats the template-pool gates as the SAME population for
design purposes** (§4 below covers both with one production shape — a
template is just a finer-grained `SynthOp`-like target), but does **not**
include them in any cost estimate beyond stating they exist and are
structurally identical, because no MBPP task in the corpus has yet been
found needing a THIRD template-pool widening the way `SortBy`'s op-level gate
was — extending scope to cover them is a straightforward instance of the same
mechanism, not a new one, and is named here rather than silently folded into
the op-level count.

### 1.3 Static op inventory these gates draw from

`OP_TABLE` (`synth_enumerate.rs:289-371`) has **31 entries** today (the
earlier reassessment's "29" count predates the `DictItems`/`SortBy` rung).
Every name a gate can `v.push(...)` must already be a row here — this
document's design (§4) treats `OP_TABLE` itself as the closed, hand-authored
PRIMITIVE population (unchanged from the earlier PREREG's Q1.3 finding) and
never proposes minting a `SynthOp` name absent from it.

### 1.4 What this ladder is NOT — kept separate on purpose

`ps_select_synthesis_operator_shape` (`seeds/program_synthesis_grounding.json`,
rule read in full) is a **different signal source**: it scores
`SynthesisOperatorShape` nodes by counting NL PROSE trigger-token matches
against `message.ps_tokens` (the task's own text), and — only when it fires —
writes `ps_enum_ops` on the Message, which `run_enumerate`
(`domains/prog_synthesis.py:1180-1186`) transcribes into `spec["ops"]`,
**overriding** the Rust ladder entirely for that call. The Rust ladder (§1.1)
is the FALLBACK used whenever `graph_ops` is empty — which per
`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md` §4.3 is every
one of the 42 named ceiling tasks and, per that document's own Rung-4 scoping,
is deliberately left to season before alignment. **This document's target is
squarely the Rust-side evidence-flag ladder (§1.1-1.2), not the NL classifier**
— the earlier PREREG's Rung 4 already claimed that territory and this design
does not duplicate or contradict it. The two are complementary: NL-prose
evidence and spec-value evidence are different observations about the same
task, and a Γ design for the latter can coexist with an sd-loop design for
the former exactly the way `ps_enum_ops`'s single transcription point already
accepts either source.

---

## 2. Is this population Γ-shaped, precisely (not by analogy)?

CLAUDE.md's own test: *"a quantity that changes, or a set of allowed moves?"*

- **Not a quantity.** No flag in §1.1 is a magnitude, a rate, a threshold, or
  anything with a continuum behind it — every one is a boolean presence-test
  on already-discrete `Value` data (`is_dict_val`, `has_dup`, `is_listlike`),
  read once and never revised by degree. There is no sd-loop "residual
  magnitude" here to decode.
- **Is a set of allowed moves, literally.** For a fixed spec, `op_list` is
  exactly a SET of admitted `(name, arity)` pairs, built by independently
  OR-ing several evidence tests — precisely `admissible_moves`'s own contract
  (multiple productions, each independently admitting or not, union of the
  admitting set) and NOT a single-classification "which one shape is this"
  problem. This is the discriminator that matters against the earlier
  PREREG's Rung-4 design (`SynthesisOperatorShape`): that layer picks ONE
  winning shape via `ArgminUnique` and reads off a pre-associated list — a
  RECOGNITION problem, correctly sd-loop-shaped. This ladder instead lets
  several independent facts each admit zero-or-more ops directly, with no
  mutual exclusion and no "winner" — that is Γ's actual generative shape, not
  a classification dressed up as one.

**Verdict: Γ, not sd-loop, and not "neither."** This is the one part of
`OP_TABLE`'s gating this document's task brief specifically asked to
re-examine that the earlier PREREG did not evaluate (it evaluated the
Term-tree search space as a whole, §1.4 of that document, and separately
scoped the NL classifier to sd-loop alignment) — and the answer, read against
CLAUDE.md's own test with the real code in hand, is that it fits Γ correctly,
not merely by using Γ's vocabulary decoratively.

---

## 3. The Γ production shape, and where it would live

### 3.1 The real, existing Γ machinery (cited precisely, not invented)

Rust (`runners/dsl/src/grammar.rs:31-39`, read in full):

```rust
pub struct Production {
    pub src: NodePattern,      // {type_: Sym, var: Sym}
    pub edge_type: Sym,
    pub tgt: NodePattern,
    pub where_: Option<TermIdx>,
    pub weight: TermIdx,       // defaults to Lit(1.0)
    pub provenance: Sym,
}
```

`ConsistencyChecker::check_edge` (`checker.rs:53-104`) looks up
`grammar.candidates(src_type, edge_type, tgt_type)` and evaluates each
matching production's `where_` in an env binding `{src.var: src_node,
tgt.var: tgt_node}` (`production_admits`, `checker.rs:108-130`) — the FIRST
admitting production short-circuits `Admitted`.

**A real, non-empty, shipped seed production** (`seeds/abusive_u0_intent.json`,
read in full, first entry):

```json
{
  "provenance": "abusive_u0_intent:victim_attended_by_abuser",
  "src": {"type": "Agent", "var": "victim"},
  "edge_type": "attended_by",
  "tgt": {"type": "Agent", "var": "abuser"}
}
```

Loaded via `substrate/seed_loader.py:56-93` (`apply_manifest` — the Rust
`load_seed_manifest` call registers it on the Rust grammar; the Python
mirror wraps `substrate.grammar.Production`/`.add`, same file, lines 83-94).
JSON shape and load path are both cited from real, currently-shipped code —
this is the exact, only syntax this document proposes reusing.

### 3.2 What the LHS/RHS need to encode for THIS population

- **`src`**: a node representing the SPEC'S OWN SHAPE, not the spec's raw
  Value rows (Γ patterns match on graph NODE TYPES, never on arbitrary
  Rust-side `Value` content) — a new node type, `SynthSpecShape`, carrying
  the §1.1 evidence flags as ATTRS (`has_dict_value`, `has_list_of_lists`,
  `has_string_value`, `has_float_value`, `has_repeated_list_element`,
  `output_is_listlike`, `output_is_setlike`, `output_is_bare_int`,
  `is_string_shaped`, `is_list_shaped` — a direct 1:1 port of §1.1's flag
  set, one node per synthesis attempt or per recurring shape class).
- **`edge_type`**: `admits_op` (new).
- **`tgt`**: `SynthOp{name: "SortBy"}` etc — a new node type, one per
  `OP_TABLE` entry (31 static nodes, mintable once at seed-boot, never
  grown past `OP_TABLE`'s own population per §1.3's boundary).
- **`where_`**: the evidence PREDICATE over `src`'s attrs — e.g. `SortBy`'s
  TWO existing gates become TWO productions (not one production with an OR
  — Γ's own semantics already union multiple admitting productions, so the
  disjunction the Rust `if A { push } ... if B && !C { push }` ladder
  encodes today is naturally TWO separate Productions with the SAME
  `(src_type, edge_type, tgt_type)` key, exactly mirroring how
  `production_admits` already treats "any one matching production admits"
  as the semantics, `checker.rs:87-93`):
  - `Eq(Attr(spec, "has_dict_value"), 1)` → admits `SynthOp{name:"SortBy"}`
  - `And(Eq(Attr(spec,"has_list_of_lists"),1), Not(Eq(Attr(spec,"has_dict_value"),1)))` → admits `SynthOp{name:"SortBy"}`

This is a faithful, lossless port of the two REAL gates read in §1.1 — not a
paraphrase, and not a simplification that drops the deliberate
non-widening of `DictItems`/`Reverse` under the second gate (each stays its
own Production with its OWN `where_`, so `DictItems`/`Reverse` simply never
get a second Production and stay exactly as narrow as today).

### 3.3 Where it would live

A new seed, `seeds/program_synthesis_opgrammar.json`, with a top-level
`"productions"` array in exactly `abusive_u0_intent.json`'s shape (§3.1),
depending on the `program_synthesis` seed the same way every other
`depends_on` edge in this tree is declared (CLAUDE.md's own "seeds are
modular with dependencies" section). Loaded through the SAME
`apply_manifest`/`load_seed_manifest` path every other seed already uses —
no new loader code.

---

## 4. Would this actually be CHECKED — or is it the same unenforced gap
   `SHAPE_AUDIT.md` already found?

This is the sharpest honesty test the task brief asks for, and the answer is
genuinely good news, found by reading the PyO3 surface directly rather than
assumed:

- `SHAPE_AUDIT.md §4` (`docs/research/engine_substrate/SHAPE_AUDIT.md:999-
  1011`) found 159/634 rule-carrying seeds mint edges via a rule's
  `add_edge` EFFECT, which — per that audit's own caveat, honestly
  unconfirmed at the engine level — likely never calls `check_edge` at all;
  the edge just gets written.
- **This design does not have to repeat that shape, and the reason is
  concrete, not aspirational.** `runners/dsl/src/py.rs` already exposes,
  on `Substrate`, three admissibility PROBES that call INTO
  `ConsistencyChecker::check_edge` (confirmed by reading `checker.rs`'s own
  call sites: `substrate.rs:1541`, `:1838`, `:1863`, all reached from these
  PyO3 methods):
  - `is_edge_admissible(src, edge_type, candidate_tgt_type, candidate_tgt_attrs)
    -> bool` (`py.rs:7922-7937`) — checks a PROSPECTIVE target that need not
    exist as a node yet (attrs passed inline). This is the cheapest fit: no
    `SynthOp` nodes need to be materialized at all — call once per candidate
    op name (`{"name": "SortBy"}`), 31 calls worst case per spec.
  - `admissible_edges_from(src, edge_type, candidates: Vec<NodeID>) ->
    Vec<NodeID>` (`py.rs:7939-7956`) — batches over EXISTING target nodes;
    usable if the 31 `SynthOp` nodes ARE materialized once at seed-boot
    (cheaper per-call, one round trip instead of 31).
  - `admissible_moves(src, edge_type, candidates: Vec<(type, attrs)>) ->
    Vec<(type, attrs, weight)>` (`py.rs:7958-7986`) — the general form,
    also usable.
- **Neither `eval_synth_enumerate`'s `EvalCtx` (`term.rs:2561-2586`, read in
  full — carries `graph: &TypedGraph` but NO `Grammar`/`ConsistencyChecker`
  field) nor any DSL `TermNode` exposes `check_edge` to the evaluator
  itself** (grepped `runners/dsl/src/term.rs` for `AdmissibleMoves`/
  `CheckEdge`/`CheckAdmi`/`GammaCheck`: zero matches). So this Γ check
  CANNOT run INSIDE the Rust `SynthEnumerate` Term evaluation today — it can
  only run from the PYTHON layer, before the `SynthEnumerate` call, using
  the already-exposed `Substrate` methods above.

**This is the actual design commitment that makes the difference between
"real Γ" and "Γ-flavored decoration," and it must be honored precisely:**
`prog_synthesis.py::run_enumerate` computes the `SynthSpecShape` attrs,
calls `is_edge_admissible`/`admissible_edges_from` per candidate `SynthOp`,
and uses the RETURNED admitted set to populate `spec["ops"]` — reusing the
EXACT existing `graph_ops`/`ps_enum_ops` transcription branch
(`prog_synthesis.py:1180-1186`) that `SynthesisOperatorShape` already
populates today, just from a second, independent evidence source. **No rule
anywhere is permitted to `add_edge` an `admits_op` relation directly** — that
would exactly reproduce the 159/634 defect one seed at a time. This
constraint costs nothing extra to satisfy (the PyO3 calls already do the
right thing) but is easy to violate by accident if a future author reaches
for the more familiar rule-effect idiom instead of the probe call, so it is
recorded here as the one discipline this design depends on.

**Net finding: unlike the humanoid composer and the 159-seed population,
this specific site does NOT need new admissibility-evaluation machinery in
the enumerator — the checking path already exists and is already exposed.**
What is missing is upstream of the check (§5): the node types to check
against, and the evidence to write onto them.

---

## 5. Is `problem_shape.py`'s `_AXES` idiom directly reusable?

Read in full (`domains/problem_shape.py:1-140`). **Yes, the SHAPE of the
idiom transfers cleanly; the SIGNAL SOURCE does not, and that gap is the
real cost.** `goal_signature` (lines 90-116) is pure mechanical extraction
from attrs a Goal ALREADY carries on the graph (`at.get("bound")`,
`native.neighbours(goal_node, "targets_mt")`) — the Goal is already a graph
node with those facts written on it by `mint_solve_*_goal` at MINT TIME
(`domains/solver_dispatch.py:174-211`, cited by `PROBLEM_SHAPE_CAN_AXES_
RESULTS.md` §2). `signature_key` (117-136) is the same "sorted
predicate=value join" idiom `sd_mint_quantum`'s own `capability_keys` uses.

The gap: a `SynthEnumerate` spec's evidence flags (§1.1) are computed
INSIDE Rust, from raw `Value` rows that are never graph nodes at all — the
spec arrives at `eval_synth_enumerate` as a `Lit`-wrapped list of dicts
(`prog_synthesis.py:1172-1176`, `spec["examples"] = {"type":"Lit","value":
rows}`), not as a graph object with `at.get(...)`-readable attrs the way a
`solve_*` Goal already is. **There is no `SynthSpecShape`-equivalent node on
the graph today for any `SynthEnumerate` call — this has to be minted new**,
unlike `ProblemShape`, which reused an ALREADY-EXISTING Goal node and only
added axes to its signature function. This is the single largest asymmetry
between this design and its cited precedent, and it is the direct cause of
decision (2) in the headline (§7).

---

## 6. The MINT mechanism — real, but a different cost class than the sd loop

### 6.1 The methodology already exists, done by hand

`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md` §3.1 (read in full) IS
the mint methodology, executed manually: force a candidate op
(`ops=["SortBy"]`) into a failing task's spec, check `found:true`, then
independently confirm the winning term against BOTH revealed rows AND the
held-out row (`substrate_rs.Substrate()._inner.evaluate`, direct call). On a
positive result, a human wrote the Rust `if` gate. **This is exactly the
sd-loop's own recognize→residual→mint discipline, one level up**: "recognize"
= the currently-admitted `op_list` fails to find a witness; "residual" = a
currently-INADMISSIBLE op, force-included, DOES produce a held-out-verified
witness; "mint" = a new Production admitting that op for that spec's shape
class.

### 6.2 Designing it as an automatic sweep, not a live rule

Unlike `sd_mint_quantum` (`seeds/shape_decode_loop.json`, read in full) —
which mints from a CHEAP graph pattern-match already computed within one
`run_rules()` fixpoint tick, guarded by a novelty check
(`Not(Exists(NodesOfType('CapabilityAxis'), induced==1 AND capability_keys
==obs.key))`, the exact `Not(Exists(...))` idiom `seeds/gap_awareness.json`
also uses for its own dedup guards, e.g. `note_unresolved_topic_gap`'s
content-dedup guard) — a residual HERE costs a full `SynthEnumerate` search
run per (failing task, candidate op) pair, because "does this op produce a
held-out-verified witness" is not decidable from graph structure alone; it
requires actually searching. **This is real, honest daylight between this
design and the sd loop's usual cost profile, and this document states it
plainly rather than importing the sd-loop's "cheap mint" reputation by
association.**

Bounded sizing: `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_3_RESULTS.md` §2
gives the real currently-failing population — 99 tasks `gapped:
enumerate_failed`. A bounded sweep (NOT all 31×99 = 3069 combinations) is
tractable: for each failing task, only try ops NOT already in its typed
default bucket but which ARE plausible for its `is_listlike`/output-type
class (e.g., a scalar-shaped spec never needs `Intersect`) — the same
typed-narrowing discipline §1.1's own branches already apply, cutting the
per-task candidate set to low single digits in practice (task 64 needed
exactly one: `SortBy`). This keeps the sweep in the tens-to-low-hundreds of
enumerate calls, not thousands, but this document does NOT claim a measured
number — it is a design-time bound, not a priced one, and should be measured
on the first slice (§8) before being trusted.

### 6.3 The guard, mirrored precisely

A residual mints a Production only when: (a) the forced-in op produces
`found:true` AND held-out-row agreement (the CEILING_REASSESSMENT_3 bar,
not merely `found:true` — `PROGRAM_SYNTHESIS_ARC6_TIER0.md`'s own headline
finding, cited by the earlier PREREG §5.1, is that inventory success and
verdict acceptance are separate gates and only the stricter one should mint
anything), AND (b) no existing Production already admits that
`(spec-shape-class, op)` pair — the `Not(Exists(...))` idiom, applied to
Productions instead of `CapabilityAxis` nodes.

### 6.4 Where this sweep would run

Not inside `run_rules()` (too expensive for a per-tick fixpoint pass).
Correct home: an offline script in the same family as
`scripts/ceiling3_diag_sweep.py` (already the tool CEILING_REASSESSMENT_3
used to enumerate the failing population), run periodically or on-demand —
mirroring how the sd loop's OWN growth is triggered by observation ticks but
this population's growth is triggered by a deliberately batched search
sweep. This is a genuinely different invocation model from the rest of the
sd-loop family and should be named as such, not silently assimilated.

---

## 7. Honest cost sizing

| piece | exists today? | cost if built |
|---|---|---|
| `Production`/`Grammar`/`ConsistencyChecker` machinery | YES, unchanged | zero |
| `is_edge_admissible`/`admissible_edges_from`/`admissible_moves` PyO3 probes | YES, unchanged, already call `check_edge` | zero — this is the one piece of good news that keeps this design cheap |
| Seed JSON syntax for productions | YES, precedent cited (§3.1) | zero — reuse verbatim |
| `SynthSpecShape` node type | NO | new — one node type, ~10 attrs, minted once per `run_enumerate` call (or once per RECURRING shape class, deduped by `signature_key`-style join, to avoid a fresh node every call) |
| `SynthOp` node type (31 static nodes) | NO | new — cheap, seed-boot-time, mirrors how other seeds mint one node per vocabulary item |
| Evidence-flag computation reaching Python | NO — flags are computed INSIDE `eval_synth_enumerate`, never returned or exposed | **the real fork in the road**: (a) duplicate the ~11 predicates in Python from the raw example rows (cheap, ~30 lines, but a SECOND place computing the same fact — exactly the drift risk `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`'s own Q1 names for `NATIVE_ORACLES`), or (b) refactor `eval_synth_enumerate`'s flag block into a small helper and expose it as a new PyO3 method returning the flag dict, so Rust stays the single source of truth. (b) is architecturally correct and NOT permitted in this task (zero `.rs` changes); (a) is buildable today but ships a known, named liability. **This decision should be made explicitly by the orchestrator, not defaulted into by drift** — hence "NOT-YET-READY to build blind." |
| `run_enumerate` wiring to consult the probe and populate `spec["ops"]` | Partially — the exact transcription branch already exists (`prog_synthesis.py:1180-1186`) for the OTHER evidence source | small — add a second producer of `graph_ops`, or a merge step; genuinely small, same shape as existing code |
| Mint sweep script | NO, but the search+held-out-row methodology exists as prior art (CEILING_REASSESSMENT_3) and a diagnostic sweep tool exists (`scripts/ceiling3_diag_sweep.py`) | medium — real new script, real (bounded, §6.2) compute cost per run, not free |
| Regression discipline | Existing house pattern (before/after battery, exact set-diff, canary check against known-passing ids, named 9-file suite) | reuse verbatim, no new discipline needed |

**Compared directly against the `SHAPE_AUDIT.md` 159/634 finding**: that
population's defect is that the CHECKING never happens (`add_edge` bypasses
`check_edge`). This design's defect risk is different and smaller: the
checking machinery is already correct and already exposed; what is missing
is the DATA PATH feeding it (a graph representation of the spec that does
not exist today) and a single-source-of-truth decision for the evidence
flags that this task is not scoped to make (no Rust edits permitted). This
is real, honestly non-trivial engineering, but it is NOT "the same
unenforced gap" — it would be a net IMPROVEMENT on that gap's shape if built
as specified in §4's discipline paragraph, not a repetition of it.

---

## 8. GO / NOT-YET-READY, and the buildable first slice

**Design-level call: GO.** §2 establishes this population is genuinely
Γ-shaped (a real generated multi-production set, not a recognition problem
dressed up as one) and distinct from the earlier PREREG's already-scoped
Rung 4 (NL classifier, correctly sd-loop-shaped, different evidence source).
§4 establishes the checking path already exists and is already correctly
enforced-capable — the strongest possible finding for a design like this,
and the opposite of what `SHAPE_AUDIT.md` found for the 159-seed population.

**Build-level call: NOT-YET-READY to start the full design blind** — one
named decision (evidence-flag single-source-of-truth, §7's forked row) has
two honestly different costs and risk profiles and should be made
explicitly, not defaulted. This mirrors `PROGRAM_SYNTHESIS_STRUCTURAL_
CEILING_REASSESSMENT_PREREG.md`'s own Rung-3 discipline ("price before
committing, do NOT bundle") applied to a data-plumbing decision instead of a
fixture-migration one.

**The buildable first slice, precisely scoped, and small — mirroring every
properly-scoped rung in this arc (Rung 1 before Rung 2, canary before
battery):**

1. **Duplicate (not refactor) the flag computation in Python**, accepting
   fork (a) from §7's table explicitly and naming it as a known, tracked
   liability (a comment citing this document, the same way `RUNG1_RESULTS.md`
   citations already thread through `synth_enumerate.rs`'s own comments) —
   this keeps the slice inside "zero Rust" for a first cut and defers (b)
   to a follow-on rung once the design is proven to move a real number.
2. **Mint `SynthSpecShape` (one node per `run_enumerate` call, not deduped
   yet — dedup is a §6.2 optimization, not a correctness requirement for a
   first slice) and the 31 static `SynthOp` nodes** at seed-boot.
3. **Hand-author exactly the TWO already-measured, already-shipped `SortBy`
   Productions from §3.2** — not a full port of all fourteen gates. This is
   the PARITY check: build the mechanism, prove it reproduces a fact this
   codebase has ALREADY measured and shipped by hand (`spec_has_dict_value`
   → `SortBy`, `spec_has_list_of_lists && !spec_has_dict_value` → `SortBy`),
   before trusting it with anything novel.
4. **Wire `run_enumerate` to call `is_edge_admissible` per candidate `SynthOp`
   and populate `spec["ops"]` via the SAME transcription branch `ps_enum_ops`
   already uses** — verify, on the full MBPP battery, EXACT set-diff parity
   with today's Rust-ladder-only behavior (task 64 still passes, task 475
   still passes, zero regressions, zero new passes yet — this slice is not
   expected to move the pass count, only to prove the plumbing is
   transparent).
5. **Only then**, as an explicitly separate, independently-gateable follow-on
   rung (mirroring `STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`'s own Rung
   2/3 separation): run the bounded mint sweep (§6.2-6.4) over the 99-task
   `gapped:enumerate_failed` population and check whether it independently
   REDISCOVERS the `SortBy`/task-64 finding as an automatic mint — this is
   the actual "would this have caught the gap automatically" proof the task
   brief asks for, and it should be measured, not assumed, before claiming
   the mint mechanism works.

**Explicitly NOT in this first slice**: porting all fourteen §1.1 gates,
porting the §1.2 template-pool gates, deciding (a) vs (b) permanently,
retiring the Rust ladder (it stays as the fallback for any shape class not
yet covered by a Production, exactly the way `DEFAULT_OPS`/typed defaults
already are the fallback under an empty `ps_enum_ops` today — a Γ miss must
degrade to today's behavior, never to zero ops).

---

## 9. What this document does NOT establish

1. **No code was written or run.** `git diff --stat c5aea7b` in this
   worktree is empty for every tracked source file — confirmed directly
   before writing this section (`git status` shows only the two new
   docs under `docs/research/program_synthesis/`, both untracked until this
   commit).
2. **The §6.2 sweep-size bound (tens to low hundreds of enumerate calls) is
   a design-time estimate, not a measurement** — the first slice's Step 5 is
   the actual measurement, and this document explicitly says not to trust
   the estimate until then.
3. **The (a)-vs-(b) evidence-flag duplication decision is deliberately left
   open** — this document names the tradeoff precisely but does not resolve
   it, per its own NOT-YET-READY call.
4. **The §1.2 template-pool population is enumerated and its structural
   identity to §1.1 is argued, but no production design was written for it**
   — named as future scope, not sized.
5. **Whether a Γ-mediated op-list actually moves the 48/257 (or current)
   MBPP pass count is unmeasured** — this design's own first slice (§8) is
   explicitly a parity check, not a capability gain; any gain would come
   only from the follow-on mint-sweep rung, and even that is bounded by
   `OP_TABLE`'s closed primitive population (§1.3/§3.2's boundary) — it can
   only ever rediscover admissibility for OPS THAT ALREADY EXIST, never
   invent a new one, exactly as CLAUDE.md's own "primitive in Rust" pathway
   and the earlier PREREG's Q1.2/Q1.3 findings require.
6. **This document does not re-verify the earlier PREREG's own findings**
   (Q1-Q4, already landed) — it extends Q1.3/Q1.4 to a question those
   sections explicitly left open, and cites them rather than re-deriving
   them, per this task's own instruction.

---

## Reproduce (read-only; nothing here writes to the graph or the engine)

```bash
cd /home/matt/ozmadev/ocelot-worktrees/oplist-admissibility-grammar
git log --oneline -1   # on top of main @ c5aea7b
git diff --stat c5aea7b   # empty for every tracked source file
sed -n '1666,2036p' runners/dsl/src/synth_enumerate.rs   # the full gate ladder
sed -n '2460,2585p' runners/dsl/src/synth_enumerate.rs   # the template-pool gates
sed -n '1,40p' runners/dsl/src/grammar.rs                # Production/Grammar
sed -n '1,131p' runners/dsl/src/checker.rs                # check_edge
sed -n '7920,7990p' runners/dsl/src/py.rs                 # admissibility probes
sed -n '1,140p' domains/problem_shape.py                  # the _AXES precedent
sed -n '1128,1260p' domains/prog_synthesis.py              # run_enumerate / ps_enum_ops
python3 -c "import json; print(json.load(open('seeds/abusive_u0_intent.json'))['productions'][0])"
```
