# Γ bulk transcription: the remaining op-list evidence-gate sites — PREREG

Builds on `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` (design, §1.1 table +
§3.2 recipe) and `OPLIST_ADMISSIBILITY_GRAMMAR_SLICE1_RESULTS.md` (the
already-shipped, already-merged 2-production `SortBy` slice, on `main`), per
`PROGRAM_SYNTHESIS_META_SKILL_ASSESSMENT_PREREG.md` §6 recommendation #1.
Base `main @ 50bde6c` ("Add meta-skill assessment..."), verified via
`git log --oneline -1 main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-gamma-bulk-transcription`,
branch `progsyn-gamma-bulk-transcription` — **not merged, not pushed**, left
for the orchestrator.

**This is a plumbing/coverage move, not a capability move.** Γ productions
are recorded facts, never consulted by `run_enumerate`'s real op-list
construction (unchanged from the SLICE1 precedent's own scoping, its own
named residual #41 in the assessment doc). **Zero MBPP task-id changes are
expected or acceptable** — any deviation is a bug to find, not a bonus.

---

## 1. Re-verified against CURRENT `main` (source has moved since both cited
   docs were written)

`OP_TABLE` (`runners/dsl/src/synth_enumerate.rs:291-413`, counted
programmatically): **57 entries**, not the SLICE1 doc's own "52" — 5 more
have landed since (`IntersectAll`, `UnionAll`, `DictFromPairs`, `Mod`,
`Sqrt`), confirmed by diffing `OP_TABLE`'s live names against the seed's
52 `SynthOp` nodes. This is the SAME staleness pattern SLICE1_RESULTS.md §7
named explicitly ("any future rung that reads an op-count from a document
rather than re-deriving it risks repeating this exact defect a fourth
time") — repeated here, corrected here. **This rung mints the 5 missing
`SynthOp` nodes** (bringing the static population to 57, matching the seed's
own stated invariant "one node per REAL current `OP_TABLE` entry") even
though none of the 5 is admitted by any of the 12 gates ported below — this
keeps the seed's own documented invariant true rather than let it drift
further, and costs nothing (static, seed-boot-time nodes).

The op-list evidence-gate ladder (`eval_synth_enumerate`,
`runners/dsl/src/synth_enumerate.rs:2093-2408`, read in full) has grown
since `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` was written: a NEW
`spec_output_is_dictlike`-gated branch (`DICT_DEFAULT_OPS`:
`Eq,IfThenElse,GroupCount,DictMerge,DictFromPairs`) was inserted into the
`if`/`else if` chain between the list-shaped branch and the final bare-
scalar fallback (the `GroupCount`/`DictMerge` rung, landed after the
design doc's §1.1 table was written). **This branch and its two op names
(`GroupCount`, `DictMerge`) are explicitly OUT OF SCOPE** — they are not
one of the 14 sites the design doc's table names, and porting them would be
scope creep into an un-costed 15th gate. They matter to this rung only
insofar as their INSERTION into the `if`/`else if` chain changed which
flag combinations reach the bare-scalar fallback branch (§3 below).

## 2. The real gate population: 14 sites, re-derived from current source,
   re-confirmed against the design doc's own table

Re-reading `eval_synth_enumerate` end to end and counting every
`v.push`/`v.extend`/bucket-selection site gated by one of the design doc's
11 evidence flags (excluding `spec_has_string_list_elements` /
`spec_has_float_list_elements`, which the design doc's own §1.2 confirms
are template-pool-only and **never feed `op_list`** — correctly excluded
from this population entirely, not merely deferred):

| site | evidence (current line) | admits | status |
|---|---|---|---|
| A | `spec_is_string_shaped` (2100) | `DEFAULT_STR_OPS` wholesale (2245) | **port** |
| B | `spec_is_list_shaped` (2111) | `DEFAULT_OPS ∪ LIST_EXTRA_OPS` (2261-2263) | **port** |
| C | `spec_output_is_listlike` (2126), nested in B | `TUPLE_BUILD_OPS` = `TupleOf` (2264-2266) | **port** |
| D | `spec_output_is_listlike`, nested in B | `Sort` (2273-2275) | **port** |
| E | `spec_output_is_listlike ∧ spec_has_string_value`, nested in B | `Split` (2285-2287) | **port** |
| F | `spec_output_is_setlike` (2129) | `SET_DEFAULT_OPS` wholesale (2260) | **port** |
| G | `spec_has_string_value` (2139), bare-scalar branch | `Replace,Split,StrCount,Capitalize,Str,ParseInt` (2231-2232, consumed 2393) | **port** |
| H | `spec_has_float_value` (2142), bare-scalar branch | `Round` (2234-2235, consumed 2393) | **port** |
| I | `spec_has_float_value`, nested in B | `Round` (2303-2305) | **port** |
| J | `spec_has_dict_value` (2154), nested in B | `DictItems,SortBy,Reverse` (2340-2344) | **`SortBy` already shipped; `DictItems`/`Reverse` ported here (completion)** |
| K | `spec_has_repeated_list_element` (2193), bare-scalar branch | `IndexedMap` (2237-2239, consumed 2393) | **DEAD — see §3, not ported** |
| L | `spec_has_repeated_list_element`, nested in B | `IndexedMap` (2328-2330) | **port** |
| M | `spec_has_list_of_lists` (2203) `∧ ¬spec_has_dict_value` | `SortBy` (2362-2364) | **already shipped** |
| N | `spec_output_is_bare_int` (2319, inline) `∧ ¬listlike ∧ ¬string ∧ ¬float`, nested in B | `ParseInt` (2321-2327) | **port** |

14 sites confirmed (matches the design doc's own count), 2 already shipped
(M fully, J's `SortBy` component only), 1 (K) found dead in current source
(§3), leaving **11 sites to newly port + 1 completion (J's `DictItems`/
`Reverse`) = the 12 the assessment doc names**, plus a 13th production this
rung adds for reasons in §4.

## 3. Site K is dead code in current source — a genuine finding, not a
   porting gap

`extra_evidence_ops` (the `Vec` sites G/H/K push onto) is populated at
lines 2231-2239, unconditionally on every call, but is only ever READ once,
at line 2393, **inside the bare-scalar `else` branch** (`v.extend
(extra_evidence_ops...)`). Site K's own guard is `if spec_is_list_shaped &&
spec_has_repeated_list_element` (line 2237) — but the bare-scalar branch is
only reached when `spec_is_list_shaped` is **false** (it is the final
`else` of the `if spec_is_string_shaped {...} else if spec_output_is_setlike
{...} else if spec_is_list_shaped {...} else if spec_output_is_dictlike
{...} else {...}` chain). So site K's condition (`spec_is_list_shaped &&
...`) can only be true in a branch where `extra_evidence_ops` is never
read. **`IndexedMap` is never admitted via this specific push, in current
source, for any spec, ever** — confirmed by tracing control flow, not
assumed. This is NOT ported as a Γ production (porting dead code would be
porting something that never fires, which is not a faithful transcription
of the LIVE ladder — the design doc's own instruction is to port what the
ladder actually does). Reported as a finding, not silently dropped.

## 4. A necessary 13th production, beyond the 12: the bare-scalar
   `DEFAULT_OPS` baseline

The design doc's own table frames `spec_is_list_shaped` (site B) as
selecting "the `DEFAULT_OPS ∪ LIST_EXTRA_OPS` branch **vs. the plain-
`DEFAULT_OPS` fallback**" — i.e. `DEFAULT_OPS`'s 12 arithmetic ops
(`Plus,Times,Minus,Div,Min,Max,Abs,Neg,Gt,Lt,Eq,IfThenElse`) are admitted
via TWO different branches, not one: the list-shaped branch (site B, ported
below) AND the bare-scalar fallback (`else`, line 2392,
`DEFAULT_OPS.to_vec()` unconditionally once that branch is reached). A
plain-arithmetic MBPP spec ("add two numbers") is exactly this second,
extremely common case. **Omitting this second admission path would make
every bare-arithmetic spec in the parity sweep (§6) show a false Γ-vs-Rust
mismatch on all 12 `DEFAULT_OPS` names** — not an edge case, the majority
shape of the simplest tasks in the corpus. This is ported as its own 13th
production, gated on the bare-scalar branch's real reachability condition:
`¬is_string_shaped ∧ ¬output_is_setlike ∧ ¬is_list_shaped ∧
¬output_is_dictlike` (§5's `output_is_dictlike` addition, needed precisely
for this exclusion — the `DICT_DEFAULT_OPS` branch, §1, sits between the
list-shaped branch and this fallback in the `if`/`else if` chain, so
reaching the fallback now requires it be false too, unlike when the design
doc's table was written).

## 5. One new flag: `output_is_dictlike`

`_synth_spec_shape_flags` (`domains/prog_synthesis.py:1153-1264`, read in
full) already computes **all ten** of the design doc's named flags —
`has_dict_value`, `has_list_of_lists`, `has_string_value`,
`has_float_value`, `has_repeated_list_element`, `output_is_listlike`,
`output_is_setlike`, `output_is_bare_int`, `is_string_shaped`,
`is_list_shaped` — **none is a placeholder**; the earlier SLICE1 rung
already built the full set even though it only consumed two of them. This
rung adds an **eleventh**: `output_is_dictlike` (direct 1:1 port of
`spec_output_is_dictlike`, `synth_enumerate.rs:2164`,
`outputs.iter().all(is_dict_val)`), needed solely for the §4 exclusion
above — it does NOT admit any `DICT_DEFAULT_OPS`-bucket op (that bucket
stays entirely out of scope, §1).

## 6. Branch-reachability exclusions: not decorative, empirically real

Sites C/D/E/I/L/N/J-completion are all textually nested inside the
`else if spec_is_list_shaped { ... }` arm. Naively porting each one keyed
ONLY on its own local flag (e.g. "`spec_output_is_listlike` → admits
`Sort`") is **provably wrong**, not merely imprecise: `spec_output_is_
setlike ⟹ spec_is_list_shaped` always holds (a Set/FrozenSet output is
`is_listlike` by construction, `synth_enumerate.rs:517-519`, so it always
satisfies `is_list_shaped`'s own first disjunct) — meaning **every
Set-output spec also has `is_list_shaped=true`**, and since `spec_output_
is_setlike` is checked earlier in the `if`/`else if` chain, such a spec
never reaches the list-shaped branch's own pushes at all; it gets
`SET_DEFAULT_OPS` instead. A production for site D lacking `¬output_is_
setlike` would therefore wrongly admit `Sort` for every one of the corpus's
Set-shaped specs (tasks 232/473 per prior docs) via TWO independent,
disagreeing productions (site D's overly-broad one, and site F's correct
one) — not a rare theoretical edge case, a structural certainty for this
exact evidence pair. **Every site nested in the list-shaped branch (C, D,
E, I, L, N, and the J-completion) is therefore given an explicit
`¬output_is_setlike` conjunct.**

The already-shipped `SortBy` productions (sites J's `SortBy` half and M)
do **not** carry this exclusion. Whether this is a live, corpus-manifesting
gap in the ALREADY-MERGED code, or a theoretical-only gap that never fires
on real MBPP specs, is answered empirically in §6 of the RESULTS doc (not
assumed either way) — this rung does not touch the two shipped productions
regardless of the answer (out of scope: they are merged, reviewed, and this
rung's job is the other 12/13, not revising shipped work), but the finding
is reported precisely either way.

## 7. Production design: one production per SITE using `In`, not one per op

The 2 shipped productions used `Eq(Attr(op,"name"), Lit("SortBy"))` because
each admits exactly one op. A bucket site (A, B, F, G, J-completion) admits
several ops under the SAME evidence predicate. `Production.tgt` matches by
node TYPE only (`grammar.rs:20-26` — confirmed, cited already in SLICE1's
own §2.3 finding), never by attrs, so a bucket CANNOT be expressed as "one
production whose tgt pattern covers N ops" — the op-specificity has to live
in `where_` regardless. Two ways to encode "op is one of these N names" in
`where_`: (a) N productions, each `Eq(op.name, "X")` conjoined with the
same evidence predicate (mirrors the shipped precedent literally), or (b)
ONE production per site using `In(Attr(op,"name"), Lit([N names]))`.

**(b) is chosen.** `TermNode::In` is a real, already-shipped Term
(`term.rs:51`, evaluator `term.rs:5029-5045`) already used this exact way
— member-of-a-literal-list — in `where` clauses across the live seed
corpus (`seeds/conversation_capability_route.json`,
`seeds/conversation_attachment_reply.json`, `seeds/conversation_topic_
reply.json`, `seeds/conversation_grice.json`, read directly, not assumed),
so it is an established idiom for exactly this shape, not a novel
mechanism. `jsonio.rs::grammar_from_json` (79-130, read in full) parses a
production's `where_` via the SAME generic `term_from_json` used for Rule
`where` clauses — no restricted Term subset for Productions — and
`checker.rs::production_admits` (108-130, read in full) evaluates it via
the SAME `evaluate()` used everywhere else. `In`'s non-text fallback path
(`c.contains(&m)`, `term.rs:5044`) does a `Value`-variant equality scan; a
plain JSON string decodes to `Value::Str` (`persist.rs:158`) and a plain
JSON array decodes to `Value::Tuple` of the same (`persist.rs:159-168`) —
both `Attr(op,"name")` and each element of `Lit([...])` decode through the
identical path, so membership equality is exact, no coercion gap. This
keeps the production count at 13 (one per site, per §2/§4) instead of the
~90 a one-production-per-op transcription of a 26-op bucket (site B) would
require, without deviating from any established idiom — `In` is already
load-bearing elsewhere in this exact seed family, just not yet in a
`Production`.

## 8. What this document does NOT establish (pre-registered, before any
   code is written)

1. Whether the ALREADY-SHIPPED `SortBy` productions' missing `¬output_is_
   setlike` exclusion (§6) ever manifests as a real mismatch on the 257-task
   corpus — an empirical question for the RESULTS doc's parity sweep, not
   assumed here in either direction.
2. Whether `In`'s membership semantics hold under every possible attr
   encoding this codebase could produce (e.g. a `Surface(Text)` name attr
   instead of `Str`) — checked only for the plain-JSON-string path actually
   used by this seed's own `SynthOp{name}` nodes and `Lit` literals, not a
   general claim about `In` everywhere.
3. Whether extending `_synth_spec_shape_flags` with `output_is_dictlike`
   is itself free of its own duplication-drift risk — it inherits the
   SAME fork-(a) tracked liability the function's own docstring already
   names for the other ten flags, not a new risk class.
4. Whether the parity check passes — that is what the RESULTS doc measures,
   not asserted here.
