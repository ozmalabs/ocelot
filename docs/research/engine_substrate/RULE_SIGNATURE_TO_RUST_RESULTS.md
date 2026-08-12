# Rule signature → Rust — results

Companion to `RULE_SIGNATURE_TO_RUST_PREREG.md` (read first — it registers
AR1–AR5 and, in §"What was read BEFORE this doc was written", exactly which
of the answers below were already suspected at registration time).

Subject: `SHAPE_TYPE_VOCABULARY_SPIKE.md` §10.1's **"largest unpriced item
in the whole arc"** — the `where`-clause signature computation that
`_pick_acting_rule` / `_pick_reply_rule` have read in production since
`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` Part 1, and which was Python.

**Worktree:** `/home/matt/ocelot-rule-signature-to-rust`, branch
`rule-signature-to-rust`, detached from `main` at `b5a235e`.
**Engine UNCHANGED — no Rust added, no rebuild:**
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`8963fb4dccaad4f8b07550ac8c8000583a5350f9d1d07d7057850b922a35f115`
(identical before and after).

---

## The one thing worth reading if you read nothing else

**The spike asked for the wrong thing, and this rung can show that rather
than assert it.** §10.1 says the signature "wants to be a Rust Term"
*because* being Python makes it un-self-repairable. But a Rust Term body is
**exactly as unreachable** to the agent's Experiment→judge→adopt machinery
as a Python body is — moving the algorithm into `term.rs` would have moved
the opacity, not removed it, while spending a Rust variant and an engine
rebuild to do it. The payoff §10.1 actually names needs the computation to
be **graph data**, and the substrate already has a way to hold an algorithm
as graph data: hub Program IR (`Prog*` Terms) executed by `ProgEval`.

So: the algorithm was rewritten inside the P1 Program-IR subset
(`domains/rule_signature_program.py`), emitted by the existing
`domains/prog_ir_emit.py`, **installed in the graph as a Term subgraph**
(857 nodes), **read back out of the graph**, and executed by the Rust
`ProgEval` interpreter — **byte-identical to the Python `rule_signature` on
all 2930 gated cases** (2917 real seed `where` clauses + 13 synthetics),
with the 40-probe production oracle's 72 rows **byte-identical to the
committed post-wiring baseline**. **Zero new Rust Term variants. Zero
engine changes.**

And the honest sting: **this rung was sent to price one unpriced item and
found two bigger ones on the way.** Both are engine defects the P1 subset
walked straight into, neither previously named anywhere in this tree:

1. `cmp_value` has **no `(Surface, Surface)` arm**, so any two
   runtime-BUILT strings compare `Equal` — and since `make_set` /
   `make_frozenset` dedup by `cmp_value` and `Value::Dict` is a cmp-sorted
   vec, **a set or dict of computed strings collapses to one element.**
   Measured: `{f"a{i}" for i in range(3)}` → `frozenset({'a0'})`.
2. `cmp_value`'s `(Str, Str)` arm compares **interner symbol IDs**, so
   `sorted`/`min`/`max`/`Lt` over strings are boot-history order, not
   lexicographic — there is no lexicographic string order in the engine at
   all.

Neither is caused by this rung; both are load-bearing for anything that
computes over strings inside the graph, which is what "move computation
into the graph" means. See §5.

---

## Verdict table

| bar | verdict | headline |
|---|---|---|
| AR1 — does the existing Term algebra suffice? | **YES, via route R3** (Program IR + `ProgEval`) | zero new Term variants; R1 and R2 enumerated as structurally insufficient, §1 |
| AR2 — real cost of a new Term variant, vs precedent | **MEASURED, and the cost table's "high / language-extension rung" is an OVERESTIMATE of the plumbing** | 6 mechanical edit sites in 3 files + one generator re-run; the real cost is the `--release` rebuild, §2 |
| AR3 — GO / NO-GO | **GO-A** (registered condition met in full) | §3 |
| AR4 — live demonstration | **MET on all four sub-bars** | 2930/2930 byte-identical; 72/72 oracle rows identical to the committed post-wiring baseline; program read back out of the graph; Python left as the test oracle only |
| AR5 — no regression | **CONFIRMED, byte-identical failing-node-id LISTS** | §6 |

---

## §1 AR1 — the existing algebra suffices, and which route

The prereg enumerated three candidate routes. All three were investigated;
two fail for structural reasons worth recording, because "we tried the
obvious thing" is the part a later reader cannot reconstruct.

**R1 — the shape-math family (`AntiUnifyWitness` / `Substitute` / `Covers`
/ `StructSim`): INSUFFICIENT.** `AntiUnifyWitness` genuinely does emit
path-addressed data (its `sigmas` are position-PATH → subterm Dicts), which
is why it was a candidate. But it emits a path only where instances
*disagree* — it is a difference operator over a COLLECTION, and the lgg of
a single value is that value, with no WILDs and therefore no paths. There
is no composition of these Terms that enumerates *every* node of *one*
tree, and none of them can express first-appearance-order variable
numbering (a stateful DFS fold), because the DSL is a pure expression
language with no recursion combinator and no user-defined function.

**R2 — graph reflection (`reflect.rs::term_to_subgraph`): INSUFFICIENT for
the same missing piece.** A where clause already reflects into `Term.<V>`
nodes with `child.<field>` edges, so the *nodes* are enumerable
(`NodesOfType`, `Neighbours`). What is not expressible is the ROW's `path`
— a root-relative route string, which needs an unbounded walk building a
string as it goes. `ReachableFrom` gives reachability, not routes. Same
root cause as R1: no recursion in the expression language.

**R3 — Program IR + `ProgEval`: SUFFICIENT, and already built.** The
substrate's answer to "an algorithm the graph holds" is not a Term that IS
the algorithm; it is Program IR that DESCRIBES it plus one interpreter Term
that runs it. `term.rs:2019-2075` states this contract explicitly: every
`Prog*` variant is inert under `evaluate()` and executes only inside the
fueled `ProgEval` — *"a program is a Term subgraph the agent can match,
decode, render and repair, and `ProgEval` is the one pure Dict-in →
Dict-out window onto its semantics."* That is, verbatim, the property
§10.1 was asking for.

The cost is that the algorithm must live inside the P1 subset. It did not,
and the blockers are exactly measurable (`emit_prog_ir` on the ORIGINAL
functions — reproduced as a gate,
`test_the_original_python_is_NOT_emittable_which_is_why_this_rewrite_exists`):

| function | `emit_prog_ir` verdict |
|---|---|
| `rule_signature` | `ok=False blockers=['ComprehensionDict', 'DefFn']` |
| `_collect_var_names` | `ok=False blockers=['RecvMethod:append']` |
| `_atomize` | `ok=False blockers=['CompTargetComplex', 'IsinstanceMultiType']` |
| `_is_term_node` | `ok=True predictable=True` |
| `_is_term_list` | `ok=True predictable=False` |

So the rewrite is not gold-plating — it is the measured admission price.
`domains/rule_signature_program.py::where_signature_rows` is the same
algorithm with: recursion → explicit LIFO stacks (pushing children in
REVERSE sorted-key order so the pop order reproduces CPython's pre-order
exactly, which is what fixes the alpha-rename indices); `.append`/`.add` →
`+=`; the dict comprehension expanded; `isinstance(x, (A,B))` split; and
its own lexicographic string comparator (§5.2). It emits `ok=True`,
`predictable=True`, oracles `{get, isinstance, keys, len, ord}` — every
extern has a real native oracle, so no part of it escapes back to a host
callback — into 36,064 bytes of Term JSON.

---

## §2 AR2 — what a new Rust Term variant actually costs

Answered even though AR1 came back SUFFICIENT, because the prereg
registered it and because the cost table's estimate turns out to be wrong
in an interesting direction.

**The edit set, read off the two real precedents** (found with
`git log -S` over `term.rs`; both landed this same week):

| site | what it is |
|---|---|
| `term.rs` — enum variant | the declaration + doc comment |
| `term.rs` — `evaluate` match arm | usually a one-line handoff to a module |
| `term.rs` — `copy_subtree` arm | mechanical |
| `term.rs` — children/`out.push` arm | mechanical |
| `jsonio.rs` ×3 | variant name, to-JSON, from-JSON |
| `reflect.rs` ×2 | `describe`, from-subgraph |
| `term_variants.rs` | **GENERATED** — re-run `tools/gen_term_variants.py`; `scale_audit.rs::variant_table_covers_the_enum` fails on drift |

Measured diffstats: `MetaShapeMint` (`933b413`) — `term.rs +35`,
`jsonio.rs +19`, `reflect.rs +10`, `term_variants.rs +4`, algorithm body
separately in `shape_decode.rs`. `CoversOpen` (`98644a3`) — `jsonio.rs
+10`, `reflect.rs +10`, `term_variants.rs +4`, `term.rs +329` (variant +
implementation + unit tests).

**On `NUM_TERM_VARIANTS` being "a hard array length" (the specific risk the
cost table flags):** it is a hard length, and it is **self-sizing**.
`TERM_EVALS` / `TERM_UNITS` are declared `[AtomicU64; NUM_TERM_VARIANTS]`
(array-repeat expressions, `scale_audit.rs:178-181`), so they resize with
the const; the const and the name table are regenerated mechanically from
the enum body; and a drift is a *compile/test failure*, never a silent
mis-attribution. **This is a bounded, well-precedented, twice-in-a-week
edit — not a "language-extension rung" in any disruptive sense.**

**But the label was pointing at the wrong cost.** What is genuinely
expensive about a Rust variant here is (a) the `--release` engine rebuild +
committing a 9 MB `.so` + the coherence probe, and (b) the thing the cost
table never priced at all: **a Rust body does not deliver the payoff.** The
agent's self-improvement machinery reads and varies *graph data*. Moving
this computation from `rule_signature.py` into `term.rs` would have
satisfied the letter of §10.1 ("wants to be a Rust Term") while leaving its
stated reason ("makes the signature un-self-repairable") exactly as
unaddressed as before. **The prereg registered this sub-claim before AR1's
answer was known; it survives.**

---

## §3 AR3 — GO-A

Registered condition: byte-identical on 100% of the real population, wired
production numbers unchanged, no engine rebuild. All three met (§4). **GO,
route R3, built and wired.**

---

## §4 AR4 — the live demonstration

### 4.1 Byte-identity — three-way, on the real corpus

`scripts/rule_signature_program_gate.py` runs
`CPython(rule_signature)` vs `CPython(where_signature_rows)` vs
`ProgEval(IR-read-back-from-the-graph)`:

```
cases: 2930 (13 synthetic + 2917 real seed where-clauses)
CPython(program) mismatches vs rule_signature : 0
ProgEval(IR)     mismatches vs rule_signature : 0
traps / non-halting                           : 0
max fuel steps used on any case: 4885392
GATE: PASS
```

The 13 synthetics deliberately cover what the corpus does NOT contain
(measured over all 2917 clauses: `ra`-atom Python types are
`{NoneType 537, bool 1863, float 77872, int 4664, str 158474, tuple 51}`,
and **max atom container depth is 1**) — nested lists, a
list-of-list-of-list, a dict-valued atom with unsorted keys, an empty term
list, a mixed list that is NOT a term list, repeated variables, nested
binders. Those paths exist for rules the agent AUTHORS later, and are
gated now rather than left as an untested branch.

### 4.2 Residency — the program is graph data, and that is what runs

`domains/rule_signature.py::signature_program(sub)`:
finds-or-installs a `SignatureProgram` node carrying `program_root` (a
`Value::Node` pointing at the installed Term subgraph), then **reads the IR
back with `term_subgraph_json(root)`** and hands *that* to `ProgEval`. What
executes is what the graph holds. Measured: 857 Term nodes materialised per
substrate; canonical reflect round-trip idempotent
(`add_term_subgraph → term_subgraph_json` twice, equal); the read-back JSON
equals the emitted JSON; a second call mints nothing.

**It survives a checkpoint.** `graph_to_dict` → fresh `Substrate` →
`graph_from_dict` → `signature_program` finds exactly one holder, the IR
read back equals the IR before the round-trip, and the signature computed
after reload is byte-identical. So a resumed daemon runs the program it
saved, not a freshly re-emitted one — which is what makes a repair to it
persist at all.

No unchecked edge is written: the link is an ATTR (`program_root`), because
`add_edge` correctly refuses (`Γ rejects: type 'SignatureProgram' not in
vocabulary (Type-2)`) and reaching for `add_edge_unchecked` to get around Γ
is precisely the pattern CLAUDE.md's SHAPES-not-numbers section names as a
defect. **Declaring a real Γ production for this node type is the honest
follow-up and is NOT done here** — named, not silently skipped.

### 4.3 Wired at the real production call site, behaviour unchanged

`ensure_where_signature(sub)` — the single production entry point, called
by both `_pick_acting_rule` (`reflective_faculty.py:2806`) and
`_pick_reply_rule` (`:3059`) — now mints its attr from
`where_signature(sub, …)`, i.e. from the graph-resident program.

Re-ran the 40-probe oracle end-to-end on a fresh full boot
(`scripts/rule_signature_measure.py`, unedited; 690/698 seeds; **2218
`RuleSummary` nodes minted**; output preserved as
`scripts/rule_signature_measurement_results_GRAPH_RESIDENT.json`):

| | committed POST_WIRING baseline | this branch |
|---|---|---|
| Class A (n=20) | struct 11, prod 11 | struct 11, prod 11 |
| Class B (n=20) | struct 0, prod 12 | struct 0, prod 12 |
| Class C (n=32) | agree 0.969 | agree 0.969 |

**All 72 rows compare byte-identical, pick for pick** (`production_pick`
and `structural_pick` on every row of all three classes). This is a
representation migration with zero measured behaviour change, which is the
bar AR4 set.

### 4.4 Python is left as the ORACLE, not as a live second implementation

`rule_signature` is no longer on any production path (`ensure_where_
signature` was its only production caller). It is retained, and its
docstring now says so, as the differential-test oracle byte-identity is
measured against — the same role a captured fixture plays elsewhere in this
arc. There is exactly one live implementation.

**Honest degradation, stated because it is a real semantic addition:** if
the graph-resident program traps or exhausts fuel on a clause,
`ensure_where_signature` SKIPS that node (leaves the attr unset, which the
production `Argmax` reads as an abstain — that rule's pre-wiring behaviour)
rather than filling it from a second implementation. Gated
(`test_a_trapping_clause_is_skipped_not_guessed`). Measured on the whole
seed corpus: zero such rules.

---

## §5 What this rung found that it was not looking for

### 5.1 `cmp_value` has no `(Surface, Surface)` arm — computed strings collapse in every Set and Dict

`value.rs:319-410`. There are arms for `(Str, Str)`, `(Tuple, Tuple)`,
`(Set, Set)`, `(Dict, Dict)`, … and **none for `(Surface, Surface)`**, so
two `Value::Surface(Text, …)` fall through to `_ => tag(a).cmp(&tag(b))`
and read `Equal`. `Value::make_set` / `make_frozenset` dedup with
`cmp_value(a,b) == Equal` (`value.rs:229-241`) and `Value::Dict` is a
cmp-sorted pair vec, so:

```
{f"a{i}" for i in range(3)}   →  frozenset({'a0'})      # measured, ProgEval
{"a0","a1","a2"} (literals)   →  {'a0','a1','a2'}       # correct
d[f"a{i}"] = i, i in 0..3     →  {'a0': 2}              # measured
d[("rt", f"a{i}")] = 1        →  {('rt','a0'): 1}       # measured — nesting doesn't save you
```

`PartialEq` gets the same comparison RIGHT (`(Surface(ka,ba),
Surface(kb,bb)) => ka == kb && ba == bb`, `value.rs:308`), so this is an
**Ord/Eq inconsistency**, not a missing feature: two values that are `!=`
compare `Equal` for ordering, and every container that canonicalises
through `cmp_value` silently loses members.

This is not an edge case for the direction this arc is travelling in. Any
computation moved into the graph that builds a string at runtime — a path,
a name, a key, a rendered label — and then puts it in a set or a dict, is
wrong today and gives no error. This rung routed around it (rows are
returned positionally as a Tuple; the caller makes the frozenset, which is
sound only because the row set is duplicate-free by construction). **The
fix is ~4 lines in `cmp_value`, but its blast radius is every persisted
Set/Dict containing Surface values, so it is named here and NOT done in
this rung.**

### 5.2 There is no lexicographic string order in the engine

`(Value::Str(x), Value::Str(y)) => x.0.cmp(&y.0)` (`value.rs:363`) — that
is a comparison of interner symbol IDs, i.e. of the order in which strings
were first seen in the process. So `sorted`, `min`, `max` and `Lt` over
strings are all **boot-history dependent**, not lexicographic:

```
engine  sorted(['where','source','var_name','a_zzz','b'])
     -> ['where','source','var_name','a_zzz','b']     (input order, here)
CPython                                               -> ['a_zzz','b','source','var_name','where']
```

The consequence is sharper than "different order": the same computation can
give different answers in two processes that interned strings in different
orders, so a value derived from it is not stable across boots. The
signature's variable numbering depends on key order, so
`where_signature_rows` carries its own comparator (`ord()` on `s[i]`,
selection sort, inlined twice because the subset has no functions to share
it with). That is 40 of the program's ~230 lines — a real, measurable tax
paid by every future graph-resident computation over strings, and the
strongest argument in this doc for fixing §5.1/§5.2 in the engine before
migrating anything else.

### 5.3 Cost of residency, measured not asserted

- **857 Term nodes** per substrate that runs a rule selection (installed
  once, lazily, idempotent).
- **Wall time.** 123.34s vs 1.20s for the first `ensure_where_signature`
  on a full boot (2218 rules), 0.03s thereafter — §6.1 for the profile, the
  three mitigations, and why the paired suite does not see it.
- **~230 lines of restricted-subset program** where the original was ~90
  lines of idiomatic Python, of which ~40 lines are the comparator §5.2
  forces and ~55 the stack-shaped `_atomize` §1 forces.

None of these is hidden in a footnote elsewhere: they are the price of the
computation being addressable by the agent, and a reviewer who thinks the
price is too high should say so against these numbers.

---

## §6 AR5 — no regression, paired failing-node-id lists

### 6.1 Per-rule cost profile

Every one of the 2917 real seed `where` clauses, both paths, same process:

```
n=2917
ProgEval  median=0.94ms   p90=1.71ms   p99=13.04ms   max=35907ms   total=122.9s
CPython   median=0.044ms  p90=0.111ms  p99=1.219ms   max=212ms     total=0.9s
top-5 ProgEval share of total: 83%  (102.1s of 122.9s)
```

Read this as two different facts, not one:

- **Per typical rule the cost is ~21× and sub-millisecond** (0.94ms vs
  0.044ms median). Nothing in an interactive path notices that.
- **The tail is brutal and it is five rules.** `embodied_motor_program.json`
  contains where-clauses that flatten to 83,881 / 76,429 / 50,059 / 50,057
  / 45,100 signature rows; they alone are 83% of the total. The program
  accumulates rows by `+=` on a persistent Tuple (the only accumulator the
  P1 subset offers — §5.1 rules out a set or dict), so cost is quadratic in
  rows for those outliers. `SIGNATURE_PROGRAM_FUEL = 200_000_000` is set
  ~40× above the largest measured cost (4,885,392 steps) so that fuel
  exhaustion means a pathological input, not a tight budget.

**The production number, measured on a real full boot** (`boot_core` +
`load_all_seeds`, 690/698 seeds, 2218 `RuleSummary` nodes — the same
population the 40-probe oracle run reports):

```
CPython oracle over 2218 rules            :   1.20s
graph-resident ensure_where_signature     : 123.34s   (touched 2218)
second call (idempotent)                  :   0.03s   (touched 0)
```

**That is the honest headline cost of this rung: a ~2-minute one-off on the
first rule-selection call of a fully-booted agent, where it was ~1 second.**
It is idempotent (0.03s thereafter), lazy (only an agent that actually runs
rule selection pays it), and invisible in the paired regression suite (§6.2:
471.82s after vs 510.47s before — the suite's own tests do not combine a
full seed load with rule selection often enough to hit it). It is still a
real regression and it is stated here, not buried.

**Three mitigations, one of them measured and deliberately NOT taken:**

1. **Chunked accumulation** — collect one small tuple per popped NODE and
   append that to `rows` once, instead of appending each row (the caller
   then flattens). Implemented and measured on the biggest rule:
   **36.03s → 14.36s, output still byte-identical**. Not adopted: it buys
   a 2.5× constant on a 5-rule pathological tail at the cost of making the
   graph-resident program a step further from the algorithm it mirrors, and
   this rung's product is the mechanism, not the constant. Recorded so the
   next person does not have to re-derive it.
2. **The real fix is in the engine: the P1 subset has no O(1)-amortised
   accumulator.** Every `+=` on a Tuple copies, `Value::Dict` is a
   cmp-sorted vec, and §5.1 rules out a set. So ANY graph-resident
   computation with linear-sized output is quadratic today. That is a third
   unpriced item, of the same family as §5.1/§5.2, and it is the one that
   decides whether "move computation into the graph" scales.
3. **Minting only the candidate population** (`writes_* == 1.0 AND
   skippable == 1.0`) would cut the work by ~50×, but changes which nodes
   carry the attr — an observable behaviour change, which this rung's own
   AR4 bar forbids. It needs its own rung.

### 6.2 The paired suite

Baseline captured on this worktree at `b5a235e` **before any edit**, on the
production-wiring rung's own 8 files plus the two prog-IR files this route
depends on (`tests/test_acting_variant.py`,
`tests/test_structural_variant.py`, `tests/test_self_delta.py`,
`tests/test_gap_awareness_migrated.py`,
`tests/test_self_concern_promote_migrated.py`,
`tests/test_agent_authors_new_rule_migrated.py`,
`tests/test_composers_graph.py`, `tests/test_experiment_composer.py`,
`tests/test_prog_ir_migrated.py`, `tests/test_prog_read_python_migrated.py`),
then re-run after the wiring edit:

```
BEFORE (b5a235e, this worktree):  9 failed, 215 passed in 510.47s
AFTER  (this branch):             9 failed, 215 passed in 471.82s
```

**The two sorted failing-node-id lists are byte-identical** (`diff` empty):

```
tests/test_acting_variant.py::test_close_experiment_loop_names_the_varied_acting_rule
tests/test_acting_variant.py::test_full_acting_variant_loop_offline
tests/test_agent_authors_new_rule_migrated.py::test_agent_authors_new_rule_end_to_end
tests/test_experiment_composer.py::test_full_self_experiment_loop_offline
tests/test_experiment_composer.py::test_mint_rule_fires_without_host_add_node
tests/test_self_delta.py::test_close_experiment_loop_teaches_and_is_idempotent
tests/test_self_delta.py::test_full_self_delta_loop_offline
tests/test_self_delta.py::test_skip_seeds_pick_is_discriminative
tests/test_structural_variant.py::test_full_structural_variant_loop_offline
```

All nine are the pre-existing `ModuleNotFoundError: No module named 'cv2'`
class (`substrate/world_adapter.py`'s `_perceive_regions`) the
production-wiring rung already recorded; none touches rule selection. This
list is enumerated, not counted, per CLAUDE.md's own retracted-baseline
rule. **Note the condition:** `data/` is symlinked in this worktree, which
is why the list is 9 here and 14 in the production-wiring rung's own run —
same code, different environment, exactly the trap that rule exists for.

**And the wall time did not regress** (471.82s vs 510.47s, i.e. slightly
faster — run-to-run noise, on a box that also had measurement jobs on it).
This is the fact that decides §6.1's cost question in practice: the
per-rule ~21× is invisible next to what these tests actually spend their
time on, and the pathological tail is not on their path.

New gate, run separately (not in the paired list, since it did not exist at
baseline): `tests/test_rule_signature_program_migrated.py` **18 passed**.

---

## §7 What a reviewer should look at first, and what is NOT done

**Look at first:** §5.1 — the `cmp_value` Surface defect is larger than the
item this rung was sent to price, and it is unfixed. Then §2's last
paragraph, which is the reason this rung did not build the thing the spike
asked for.

**Not done, named:**

1. **The two engine defects are NOT fixed** (§5.1, §5.2). Both are small
   patches with wide blast radius; each wants its own rung with its own
   before/after set-content measurement.
2. **No Γ production for `SignatureProgram`** (§4.2). The node is minted
   and linked by attr specifically to avoid an unchecked edge, but the
   honest form is a declared production.
3. **The Python `rule_signature` still exists** as the oracle. That is
   deliberate (byte-identity has to be measured against something), but it
   does mean the algorithm is written twice; if it drifts, the gate is what
   catches it.
4. **No Experiment→adopt cycle has been RUN against the signature
   program.** The prereg scoped that out. What is established is that the
   computation is now the KIND of object that machinery operates on — Prog
   IR in the graph — not that a self-repair of it has been demonstrated
   end-to-end.
5. **The `_atomize` generality is gated only by synthetics**, because the
   real corpus has no nested atoms (max depth 1, measured). The synthetics
   are real tests, but they are not evidence about rules that do not exist
   yet.
