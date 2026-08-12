# Rule reference layer — sizing results

Companion to `RULE_REFERENCE_LAYER_SIZING_PREREG.md` (read first — every bar
below was registered, with its prediction, before the corresponding number
existed). Resolves the three questions
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §10.3 / §10.4 and §12 items 3, 5 and 6 left
open.

**Worktree:** `/home/matt/ocelot-rule-reference-layer`, branch
`rule-reference-layer`, detached from `main` at `abae030`.

**Engine: UNCHANGED.** `_native.abi3.so` sha256
`81d75c0a84dc221839cb1d4aa9668d2064061613a225bf754cbc768c9f9b5b2e` — the
committed binary at `abae030`, byte-identical, never rebuilt. **No Rust was
written in this rung.** `git diff --stat abae030` touches exactly one
tracked path before this doc: the prereg. Coherence probe passed once at the
start (`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back
`{'tup': (1, 2, 3), 'lst': [1, 2, 3]}` — list and tuple distinct).

**Provenance caveat, stated because it would otherwise look like a defect:**
`engine_provenance()` in this worktree reports `source_match = "own"` and a
`stale_rust` list containing essentially every `.rs` file. That is a
`git worktree add` artifact — checkout sets every source mtime to now,
later than the committed `.so`'s. The source is a clean checkout of
`abae030` (verified: `git diff abae030 -- runners/` is empty) and the `.so`
hashes identically to the one committed at `abae030`. Nothing was rebuilt
and nothing needed to be.

---

## The one thing worth reading if you read nothing else

**Shape math produced a new, correct, previously-nonexistent rule from three
real rules the agent already holds — and the new rule fires exactly where
the analogy says it should and nowhere else.**

Three rules that exist in `seeds/` today sit at three corners of a
parallelogram over two independent dimensions:

|  | `decide_armed` | `observe_armed` |
|---|---|---|
| **`(town -has_actor-> maker)`** | `a` = `pd_decide` | `b` = `po_observe` |
| **`(m -is_at-> cur)`** | `c` = `af_choose_action` | **MISSING** |

One `AntiUnifyWitness` call over `[a, b, c]` returns the template and three
witnesses. The transform `T` = the a→b difference is a **single path**
(`where.a.items.0.key`: `decide_armed` → `observe_armed`). Applying `T` to
`c`'s witness and calling `Substitute` yields

```
x.match = [["m", "is_at", "cur"]]
x.where = Attr(m, "observe_armed") == 1.0
```

— **absent from all 2,851 distinct `match|where` recognisers in the seed
corpus.** Installed as a real rule and run, the full 2×2 grid comes back
clean: every cell fires exactly one rule, and the missing corner fires `x`.

```
OK   has_actor  x decide_armed   -> fired=['a']  expected=['a']
OK   has_actor  x observe_armed  -> fired=['b']  expected=['b']
OK   is_at      x decide_armed   -> fired=['c']  expected=['c']
OK   is_at      x observe_armed  -> fired=['x']  expected=['x']  <-- THE MISSING CORNER
```

**This is the creator's own framing landing, measured:** *"dedupe isn't the
win… it's the shape math. Analogical thinking is the key."* The transfer
needed **zero new Rust Terms, zero graph mirror, and zero engine change** —
the algebra has been in `term.rs` since June 2026 and nothing had ever handed
it a rule.

And it is not one lucky triple: the corpus contains **318 such
parallelograms with a genuinely missing fourth corner**, and on the 200
persisted for measurement, **200/200** are algebraically lossless, well
defined, and produce a novel `x`.

The second thing worth reading, because it decides the *other* half of the
brief: **unconditional mirroring on `add_rule` is a measured NO-GO** — it
reproduces the Γ thread's own unbounded checkpoint-growth defect at roughly
ten times the rate (+2,557 graph nodes per save/load cycle, linear, no
convergence), across a 190-file at-risk surface (Γ's was 27).

---

## Verdict table

| bar | verdict | headline |
|---|---|---|
| **RR1** — is `Covers`-with-witness needed? | **GO — zero new Term variants** | `AntiUnifyWitness` alone returns coverage, residual and bindings in ONE call. 300/300 positive and 150/150 negative on real corpus rules. **Registered prediction confirmed, including its encoding-conditionality** |
| **RR2** — `add_rule` blast radius | **NO-GO for unconditional wiring** | 190 at-risk files (enumerated, not counted); mean 133 mirror nodes/rule; 4.42× graph growth at default boot; **+2,557 nodes per checkpoint cycle, unbounded** |
| **RR3** — is lazy mirroring sufficient? | **GO** | No reasoning path needs whole-store completeness; the paths that need a rule mirrored *name* it. Plus: the lazy graph mirror **already exists and is already exposed** (`add_term_subgraph`) |
| **RR4** — build, or size | **BUILT — the transfer demonstration. `rule_reflect.rs` deliberately NOT built** | 2×2 grid, 4/4 cells correct; 318 parallelograms found, 200/200 transfers sound. Rust judged unnecessary, not deferred-by-timidity — see §5 |
| **RR5** — no regression | **CONFIRMED, zero executable diff** | 11 pre-existing reds reproduced byte-identically; `test_rules_checkpoint.py` and `test_persistence_migrated.py` (the two the Γ reroute broke) **green** |

---

## §1 RR1 — `Covers`-with-witness is NOT needed, and the spike's own encoding sketch is why the question looked open

The spike's §10.3 called this *"the first thing I would check before writing
any Rust — because 'zero new Term variants' versus 'one new Term variant' is
the difference between a wiring rung and a language-extension rung."*

**Answer: zero new Term variants. It is a wiring rung — but only under one
of the three encodings probed, and NOT under the one §5.3/§6.2 sketches.**

### 1.1 The three encodings, measured live

`scratch_rr/rr1_covers_witness_probe.py`, on `note_reported_gap`
(`seeds/gap_awareness.json` — the spike's own §6 worked example, 82
signature rows via the landed `domains/rule_signature.py`):

**Encoding A — `FrozenSet` of fully concrete rows, a slot is an ABSENT row.**

```
A1 Covers(entry, obs)                = True
A2 Covers(obs, entry)  [expect False]= False
A3 AntiUnifyWitness template rows    = 80  (== entry: True)
A4 sigma[entry] (pattern-side extra) = 0 path-entries -> EMPTY == covers: True
A5 sigma[obs]   (the RESIDUAL)       = 1 path-entries
     residual member count           = 2  (== the 2 omitted slot rows: True)
A6 Substitute(template, sigma_obs) == obs : True
A7 NEGATIVE control with 'abandon_goal_on_no_movement': Covers=False,
   sigma[pattern] non-empty=True  (agreement Covers<->empty-sigma: True)
```

One `AntiUnifyWitness` call yields **all three** things the recognise step
needs: the template (identical to the held entry), the coverage verdict
(`σ_pattern` empty ⟺ `Covers`), and the **residual** (`σ_observation`,
exactly the omitted rows) — which is precisely what `sd_recognize`'s
`Count(residual) == 0` gate and `sd_mint_quantum`'s novelty guard read.
`Substitute` rebuilds the observation exactly.

**Encoding B — the spike's own literal marked-SLOT row. FAILS.**

```
B1 Covers(entry_B, obs)  [spike assumes True] = False
B2 sigma[entry_B] non-empty (pattern leaks)   = True
     pattern-side extras = 2 (the SLOT rows themselves — read as pattern NOISE, not as holes)
B3 Covers(entry_B_wild, obs) [in-row WILD]    = False
```

Root cause, read directly: `covers_value`'s Set arm compares members with
`==` and **does not recurse into them** (`term.rs:3735`
`ps.iter().all(|m| is.iter().any(|x| x == m))`). So a row carrying a `SLOT`
atom, or a real WILD marker, is simply a *different member* — invisible as a
hole. §6.2's sketch (`("rt","…container","SLOT")` +
`("ra","…container","role","probe_a_words")`) does not work as written.

**Encoding C — `Dict` of path→atom with WILD slots. Coverage works, the
RESIDUAL IS LOST.**

```
C0 marker sanity: Covers(WILDV, 'anything')      = True
C1 Covers(entry_D, obs_D) [WILD-aware Dict arm] = True
C3 entry_D2 OMITS 2 keys (obs-only keys = the residual):
     Covers(entry_D2, obs_D)          = True
     template keys                    = 80 (obs has 82)
     sigma[obs] captures residual?    = 0 entries -> RESIDUAL LOST: True
C4 Substitute(template, sigma_obs) == obs_D : False (round-trip LOSSY)
```

`covers_value`'s Dict arm *does* recurse and *does* honour WILD, and has no
equal-length requirement — so C looks attractive. But
`anti_unify_witness_values`' Dict arm generalises over **shared keys only**
(`term.rs:3401-3404`), so observation-only keys vanish from both template and
witness. An sd loop on encoding C would report **zero residual for genuinely
novel structure** and `sd_mint_quantum` would never fire. Disqualifying.

### 1.2 The correction this forces on the design

**A slot must be an ABSENCE, not a marked row.** That is not a workaround —
it is CLAUDE.md's own "unknown = absence, first-class" principle arriving
from the other direction, and it is what makes the residual fall out of the
Set arm for free. The spike's §5.3 property list ("set semantics ⇒ no
equal-length requirement", "Occam carried by `FixedCount`") all survives;
only the SLOT-row notation in §5.3/§6.2 has to go.

### 1.3 A correction to my own probe, recorded because it nearly produced a wrong verdict

The first run of the B and C probes used the bare string `"·?·"` as the
in-data wild marker and got `False` everywhere — which would have read as
"Covers is not WILD-aware at all". It is not: a Term's `wild` **field** is a
Sym *name* (a bare string), but the wild **value** the engine compares
against inside data is `Value::Tuple([Value::Str(sym)])` — a **one-tuple**
(`term.rs:6362`). Using the field's spelling as a data marker silently never
matches. Corrected, re-run, and the B negative survived the correction while
the C1 negative flipped to `True`. Recorded because the wrong version of
this finding is *more* dramatic and would have been easy to publish.

### 1.4 Widened: is it one pair or the corpus?

`scratch_rr/rr1_corpus_sweep.py`, over 2,800 seed rules with a non-null
`where`, seeded sample of 300 positive pairs (entry := a real sub-signature)
and 150 negative pairs (unrelated rules):

```
POSITIVE pairs, n=300
  I1  Covers  <->  sigma[entry] empty          : 300/300
  I2  sigma[obs] == obs \ entry (the residual) : 300/300
  I3  Substitute(template, sigma_obs) == obs   : 300/300
NEGATIVE pairs, n=150
  I1  Covers  <->  sigma[entry] empty          : 150/150
```

**RR1: GO.** The §10.2 cost table's "zero new Rust Terms" assumption stands.

---

## §2 RR2 — the `add_rule` blast radius, measured. NO-GO for unconditional wiring.

Method: `GAMMA_PYO3_REROUTE_RESULTS.md` §1–§2, applied to `add_rule`.

### 2.1 The call-site inventory, by mechanism

The spike's §10.4 treated `add_rule` as one thing. It is four, and they have
different consequences:

| mechanism | entry point | reaches `Substrate::add_rule`? |
|---|---|---|
| PyO3 `add_rule` binding | `py.rs:3254` → `inner.add_rule` (`:3264`) | yes |
| **`import_rules` (checkpoint restore)** | `py.rs:4547` → `inner.add_rule` (`:4576`), once per rule | **yes — this is the dangerous one** |
| `load_seed_manifest`'s rules loop | `py.rs:1630` → `inner.add_rule` | yes |
| Rust inherent callers | 36 sites in `runners/dsl/src/*.rs` | yes |

Python call sites: **51 test files / 170 calls**, **34 `domains/` files / 78
calls**, **80 `scripts/` files / 123 calls**. And, dominating everything,
**800 files** reach the rule store through `load_seed_manifest` /
`load_all_seeds` / `boot_core` / `WorldAdapter()`. Γ's comparable figure was
129 call sites.

### 2.2 The at-risk subset — enumerated, per CLAUDE.md's own standing rule

**190 files** combine a rule-installation path with a node-count-shaped read
(`node_count()`/`edge_count()`, `len(...nodes(...))`, `graph_to_dict()["nodes"]`,
`rule_count()`). Γ's equivalent was 27.

**The list is the artifact, not the number** — `scratch_rr/rr2_at_risk_files.json`,
one entry per file with which shape it carries. This doc deliberately does
not restate it as a characterisation; per CLAUDE.md's retracted-baseline
rule, *a baseline must be a list, never a count.*

### 2.3 The per-rule mirror size, measured live with no engine change

`py.rs` already exposes `add_term_subgraph` — literally
`reflect::term_to_subgraph`, the exact operation a mirror on `add_rule`
would perform. So this needed no build:

```
seed rules carrying a `where` Term: 2907
Mirrored 2907 rules (0 refused by add_term_subgraph)
  TOTAL graph nodes minted by mirroring every seed `where`: 386,195
  mean per rule  : 132.9
  median         : 19
  p90 / p99 / max: 59 / 461 / 51769
  largest single-rule mirrors:
     51,769 nodes  emp_abs_expand_factorized_groups_in_parallel  (seeds/embodied_motor_program.json)
     47,133 nodes  emp_abs_expand_embodied_motor_program  (seeds/embodied_motor_program.json)
```

The spike guessed "~40 `Term.*` nodes" for a 40-node where-clause. The
**median** is 19 — so the guess was pessimistic for the typical rule — but
the **mean is 133** and one single rule mirrors to **51,769 nodes**. The
distribution is what matters, and it is exactly the embodied-seed
concentration §3 of the spike already found, reappearing.

### 2.4 §12 item 5 resolved: the LIVE rule population is nothing like the seed corpus

The spike flagged *"It does not measure the live graph… I did not boot an
agent."* Booted:

```
--- live booted agent ---
  default-boot rule slots           : 134
  of which carry a `where` Term     : 131
  graph nodes at boot               : 747
  mirror nodes for the LIVE rule population (131 rules): 2,557
  ==> mirroring would multiply this agent's graph by 4.42x
```

A default `WorldAdapter()` holds **134** rules, not 2,934 — the storage
profile overstates the live population by ~22×. But the mirror is still
**4.42× the entire graph**, because a default-boot graph is only 747 nodes.
Both halves of that are worth carrying forward: the spike's compression
numbers are less alarming than they look, and the mirror is more alarming
than they suggest.

(A full `load_all_seeds` boot is a different regime again — 2,166 rule
slots; §3.2.)

### 2.5 The unbounded checkpoint-replay defect — the Γ finding, reproduced at rule scale

`GAMMA_PYO3_REROUTE_RESULTS.md` §2.5 found that `WorldAdapter.load()`
replaying `add_production` re-minted a mirror on top of the one
`graph_from_dict` had already restored: +261 nodes per cycle, linear,
unbounded. That was fixed by adding `add_production_no_mirror`
(`py.rs:7845`), which `world_adapter.py:6181` now calls.

**The rule path has the identical structure and no such fix.**
`save()` writes `"graph": graph_to_dict()` (which would include the mirror)
**and** `"rules": export_rules()`; `load()` does `graph_from_dict(...)`
(restoring the mirror) and then `import_rules(blob["rules"])`
(`world_adapter.py:6187`), which replays `inner.add_rule` **once per rule**.
Simulated at exactly that seam, with no engine change:

```
  cycle 0: nodes=    3,304  edges=    3,172  checkpoint=0.7 MB
  cycle 1: nodes=    5,861  edges=    5,598  checkpoint=1.0 MB
  cycle 2: nodes=    8,418  edges=    8,024  checkpoint=1.3 MB
  cycle 3: nodes=   10,975  edges=   10,450  checkpoint=1.6 MB
```

**+2,557 nodes and +0.3 MB every cycle, constant, no convergence** — the
same defect shape, ~10× the Γ rate, on the daemon's own documented
checkpoint/resume operating pattern.

**RR2: NO-GO for unconditional wiring.** Both of the prereg's registered
NO-GO conditions are met independently: the growth is unbounded, and the fix
lies in `world_adapter.py` and `py.rs` — both outside this rung's registered
file scope. This is not a reason to abandon the design; it is the reason the
design must be **lazy**, which is RR3.

**Honest scope note:** this simulation reproduces the *replay* mechanism
faithfully (it mirrors at the seam `add_rule` would have, then saves and
loads). It does **not** prove that a real mirror-in-`add_rule` build would
produce these exact numbers — a real build could differ in dedup, in what
`graph_to_dict` serialises, or in `import_rules`' own ordering. What is
established is the *mechanism* and its order of magnitude, not a byte-exact
prediction.

---

## §3 RR3 — lazy mirroring IS sufficient, and the lazy mirror already exists

### 3.1 `ShapeCache` is the right idea and the wrong precedent

Read directly (`shape.rs`, `substrate.rs:148`, `:793`): `ShapeCache` is
`FxHashMap<TermIdx, Shape>` — `get` / `insert` / `assess_and_cache` (compute
on miss, memoise). It is genuinely lazy, genuinely on-demand, and — per its
own doc comment — effectively never invalidated, because a Term's structural
shape is stable for its arena lifetime.

**But it writes no graph nodes at all.** It is a Rust-internal memo table. It
is therefore a fine precedent for "compute on demand" and *no* precedent at
all for "what an incomplete graph-resident mirror does to reasoning" — which
is the question §10.4 actually needed answered.

**The right precedent is already in the tree and the spike missed it:**
`add_term_subgraph` (`py.rs:8551`) and `add_shape_node_for_term`
(`py.rs:8534`) are caller-invoked, on-demand, write-nodes-only-when-asked
graph mirrors of a Term. `add_term_subgraph` **is** `rule_to_subgraph` for
the `where` half, today, exposed, working — this rung used it to produce
every number in §2.3/§2.5. See §5 for what that does to §10.2's cost table.

### 3.2 Does any reasoning path need the mirror COMPLETE?

Measured on a full `boot_core` + `load_all_seeds` agent
(`scratch_rr/rr3_completeness_probe.py`):

```
  installed rule slots (rule_count)   : 2166
  of which carry a `where` Term       : 2146
  RuleSummary nodes in the graph      : 2208
  ==> RuleSummary mirrors 2208/2166 = 101.9% of the rule store
  flag population on RuleSummary nodes: {'writes_chosen_action': 2208}
```

**This falsified my working expectation and is the more interesting
result.** I expected `RuleSummary` to be a *partial* mirror (per the
rule-signature slice's §2, which found the acting-provenance minter skipping
names already present). It is not — `domains.self_model.ensure_self_model`
mints one per rule at boot, so the flat mirror is **complete, and slightly
over-complete** (2,208 > 2,166: names duplicated across seeds).

The reason completeness is affordable there is exactly the reason it is not
affordable for a structural mirror: a `RuleSummary` is **one flat node with
an opaque `rule_json` string**. The same completeness at Term-subgraph grain
would be 2,146 × 133 ≈ **285,000 nodes**. *Completeness and structure are
affordable one at a time, not together* — which is the sharpest single
sentence to carry out of RR3.

What the consumers actually require:

- `_pick_acting_rule` / `_pick_reply_rule` filter candidates
  (`writes_chosen_action == 1.0 AND skippable == 1.0`,
  `reflective_faculty.py:2756-2757`) and `Argmax` over the survivors. An
  absent candidate is a **recall** loss that degrades to an honest abstain —
  and on a live boot `skippable` is `None` everywhere, so the pool is empty
  and the function abstains today (the rule-signature slice's §2 finding,
  independently reconfirmed here). Nothing breaks on absence.
- The self-improvement spine operates on rules a concern *names*; it never
  enumerates the store.
- The one completeness-shaped assertion found anywhere is
  `tests/test_rule_literal_variation_migrated.py:198` —
  `assert name in by_name, f"{name} not mirrored as a RuleSummary"` — which
  requires the mirror to contain **specific named rules**, not all of them.
- The genuine hazard is the sd loop: a mint decided against an incomplete
  codebook is a duplicate. But the codebook **is** the mirrored set, so an
  unmirrored rule is not "missing from the codebook" — it is not in the
  codebook. And the loop already carries a duplicate-mint guard for exactly
  this hazard at another grain (`sd_dedup_existing`,
  `seeds/shape_decode_loop.json`, whose own comment names it as a
  novelty-guard mirror of `sd_mint_quantum`).

**RR3: GO.** Lazy, demand-driven mirroring is sufficient everywhere it would
be used — "mirror the rules something asks a shape question about" is
already the shape of `ensure_where_signature(sub)` in the landed slice, and
of `add_term_subgraph` in the engine.

---

## §4 RR4 — the analogical transfer, in full

### 4.1 Why this and not a dedup ratio

Per the creator's mid-flight framing (quoted in full in the prereg): *"dedupe
isn't the win… it's the shape math. Analogical thinking is the key."* The
spike's own §9.2 already ranks structural sharing **last** of five benefits,
and §3 shows compression is weak outside `embodied_motor_program.json`. So
the evidence this rung owes is a transfer, not a ratio.

### 4.2 The parallelogram, discovered mechanically

`scratch_rr/rr4_find_parallelogram.py` groups every seed rule's
`{match, where}` by exact tree skeleton, then searches each family for
triples `(a, b, c)` where the a→b path set **P** and the a→c path set **Q**
are non-empty and **disjoint** — the condition under which the fourth corner
is defined — and where that fourth corner is **not already a family member**.

**318 such triples exist in the corpus.** The one demonstrated:

```
  a = pd_decide         seeds/bigville_action_decide.json
  b = po_observe        seeds/bigville_action_decide.json
  c = af_choose_action  seeds/bigville_affect_decide.json
```

One `AntiUnifyWitness([a,b,c])` call, five WILD paths, three witnesses:

```
  match.0.0                  a='town'          b='town'          c='m'
  match.0.1                  a='has_actor'     b='has_actor'     c='is_at'
  match.0.2                  a='maker'         b='maker'         c='cur'
  where.a.items.0.key        a='decide_armed'  b='observe_armed' c='decide_armed'
  where.a.items.0.node.name  a='maker'         b='maker'         c='m'

  P (a->b) = ['where.a.items.0.key']                       <- WHAT IS ARMED
  Q (a->c) = ['match.0.0','match.0.1','match.0.2',
              'where.a.items.0.node.name']                 <- WHICH BINDING
  disjoint : True
```

Losslessness was checked **before** the transfer was attempted, on all three
real rules: `Substitute(template, σ_i) == i` → `True/True/True`.

### 4.3 The result, and the behavioural gate

```
x.match = [["m", "is_at", "cur"]]
x.where = Attr(m, "observe_armed") == 1.0
x != a, x != b, x != c
x is ABSENT from the whole seed corpus (2851 distinct match|where recognisers): True
```

Installed as a real rule alongside `a`, `b` and `c`, run on four graphs that
discriminate the 2×2 grid (each row binds the opposite endpoint — itself part
of dimension Q — so each cell places the armed attr on the endpoint its own
row reads):

```
OK   has_actor  x decide_armed   -> fired=['a']  expected=['a']
OK   has_actor  x observe_armed  -> fired=['b']  expected=['b']
OK   is_at      x decide_armed   -> fired=['c']  expected=['c']
OK   is_at      x observe_armed  -> fired=['x']  expected=['x']  <-- THE MISSING CORNER
```

Every cell fires **exactly one** rule. This is the bar the prereg registered:
not "x parses", but "x fires exactly where predicted and nowhere else".

### 4.4 At scale

`scratch_rr/rr4_transfer_at_scale.py`, over the 200 persisted triples:

```
parallelogram triples tested        : 200
  L  algebra lossless on all 3 rules: 200/200
  D  P and Q disjoint               : 200/200
  N  x novel (absent from corpus)   : 200/200
  ==> transfers that are lossless AND well-defined AND novel: 200/200
```

**Honest boundary:** the 200/200 measures the *algebra* — lossless, well
defined, novel. Only the one triple in §4.3 was verified *behaviourally* by
installing and firing. "200 correct new rules" is **not** claimed; "200
well-formed novel transfers, one of them verified to behave exactly as
predicted" is.

### 4.5 What this does and does not establish

- It **does** establish that the shape-math algebra already in `term.rs`
  operates correctly on real rule bodies, and that a genuinely new and
  correct rule can be derived from three held ones by MEET-then-JOIN alone.
- It **does not** establish that the agent would *choose* a useful transfer.
  Selecting which parallelogram is worth completing is the FAC-stage
  question §9.2 item 2 raises, and this rung supplies the operator, not the
  selector.
- It **does not** move any benchmark, and none is claimed
  ("synthetic-proven mechanism ≠ benchmark value, report both").
- The transfer here is over the **recogniser** half (`match` + `where`) only
  — the constructor half stays with `c`. §8 of the spike (effects have an
  order that resists set semantics) is untouched and unresolved.

---

## §5 Why `rule_reflect.rs` was NOT built — and a correction to §10.2's cost table

The prereg's GO branch permitted building `rule_reflect.rs`. It was not
built, for a reason found during the measurement rather than decided in
advance:

**`add_term_subgraph` (`py.rs:8551`) already is `rule_to_subgraph` for the
`where` half — on demand, lazily, exposed to Python, working today.** This
rung used it to mirror 2,907 real seed where-clauses (§2.3) with zero engine
change. §10.2's cost table lists `runners/dsl/src/rule_reflect.rs` as
~350–450 new lines without noticing that the generic mechanism it would wrap
(`reflect::term_to_subgraph`) is already reachable per-Term from the world
adapter. What `rule_reflect.rs` would genuinely add is the `match` and
`effects` halves plus a `rule_from_subgraph` inverse — real work, but
**smaller than sized and not on the critical path for anything this rung
measured.**

Combined with RR4 needing no mirror at all (the algebra runs on `Value`
trees, not graph nodes) and RR2's NO-GO on unconditional wiring, building
Rust here would have meant: rebuilding the engine, taking on the
stale-provenance and rebuild-last gotchas, and shipping a module nothing
calls — since `py.rs` is out of this rung's scope, a new Rust module would
have had **no Python entry point**. The prereg's own words: *"no build is to
be forced."*

**What a future rung should build instead, named precisely:**

1. **`import_rules_no_mirror`** (or a mirror-suppression flag on
   `import_rules`), the exact analogue of the landed
   `add_production_no_mirror` — this is the single change that converts
   RR2's NO-GO into a GO, and it is a `py.rs` + `world_adapter.py` rung with
   its own gate.
2. **A `kind: "rule_where"` codebook over encoding A**, populated lazily via
   `ensure_where_signature`-style demand, feeding the unchanged `sd_*` rules.
3. **The FAC stage**: `_pick_acting_rule`'s name-keyword `Argmax` as the MAC
   filter, escalating survivors to `Covers`/`AntiUnifyWitness` over the
   codebook. The rule-signature slice already measured that the two read
   different real information; RR4 supplies the operator that acts on it.
4. Only then `rule_reflect.rs`, for `match`/`effects` and the inverse.

---

## §6 RR5 — no regression

- `git diff --stat abae030` before this doc: **one file**, the prereg.
  Nothing under `runners/`, `domains/`, `substrate/`, `seeds/`, `scripts/`,
  `tests/`, or `conftest.py` was touched — verified, not asserted.
- Engine `.so` sha256 identical to the committed binary at `abae030`.
- Regression run (7 files: the rule-signature slice's own five, plus the two
  the Γ reroute broke):

```
11 failed, 50 passed, 3 warnings in 275.42s
```

The 11 are **exactly** the 11 pre-existing reds
`RULE_SIGNATURE_SLICE_RESULTS.md` §4 enumerates, same node ids, same order
(`test_acting_variant.py` ×2, `test_structural_variant.py` ×1,
`test_self_delta.py` ×3, `test_gap_awareness_migrated.py` ×5; several are
`ModuleNotFoundError: No module named 'cv2'`). **`tests/test_rules_checkpoint.py`
and `tests/test_persistence_migrated.py` — the two the Γ PyO3 reroute broke —
are green here**, which is the point: this rung demonstrated the growth
mechanism without shipping it.

---

## §7 Everything that broke, or nearly did

1. **The wild-marker error (§1.3).** Using the Term's `wild` field spelling
   (`"·?·"`) as an in-data marker instead of the one-tuple `("·?·",)` made
   every WILD-bearing probe return `False`. Caught by adding a sanity line
   (`Covers(WILD, 'anything')`) that should trivially be `True` and was not.
   **Lesson: probe your marker before you trust your negatives.**
2. **`native.evaluate` cannot carry a sigma.** A witness is a `Value::Dict`
   with position-PATH **tuple** keys; the PyO3 term-JSON wire rejects it
   (`TypeError: keys must be str, int, float, bool or None, not tuple`).
   Two ways round it, both used: compose `Substitute(IndexAt(AUW,0),
   IndexAt(IndexAt(AUW,1),i))` as one term-tree (which is what a graph rule
   would do anyway), or hand-build `persist.rs`'s `{"__dict__": [[k,v],…]}`
   tagged form. **Worth knowing for any future rung that wants σ arithmetic
   from Python.**
3. **The 2×2 grid's first run showed a false failure.** `a`/`b` bind the
   match triple's **target** var, `c`/`x` its **source** — so a harness that
   puts the armed attr on one endpoint fails the other row. That is a real
   part of dimension Q, and the fixed harness places the attr per-row. The
   first result (`BAD … expected=['b']`) was harness error, not transfer
   error; recorded rather than silently corrected.
4. **`RuleSummary` completeness falsified my expectation** (§3.2). Reported
   as measured, and it strengthened rather than weakened RR3.
5. **`stale_rust` false alarm** — a worktree mtime artifact, diagnosed, not a
   defect (see the provenance note at the top).

---

## §8 Remaining uncertainties

1. **§2.5's amplification is simulated, not built.** The mechanism and order
   of magnitude are established; exact numbers from a real mirror-in-`add_rule`
   build are not.
2. **Only one of 318 transfers was verified behaviourally.** The other 199
   measured are algebraically sound and novel; whether they are *useful* is
   not measured and not claimed.
3. **The effects half is untouched.** §8 of the spike (order-sensitivity,
   `{"__term__": …}` computed args nested inside effects) is exactly as open
   as it was.
4. **§5.4's open question (two codebooks or three) is still open** — out of
   charter, and RR1's finding does not bear on it either way.
5. **The at-risk list (§2.2) is a static grep, not a run.** 190 files carry
   the *shape*; how many would actually go red under a real build is
   unmeasured — deliberately, since RR2 reached NO-GO on independently
   sufficient grounds (the unbounded growth) and burning a multi-hour
   shared-box budget to size a rejected option would not have changed the
   verdict.
6. **No benchmark moved and none was attempted.**

---

## §9 Reproduce

```bash
cd /home/matt/ocelot-rule-reference-layer
git log --oneline -1
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   81d75c0a84dc221839cb1d4aa9668d2064061613a225bf754cbc768c9f9b5b2e (unchanged from abae030)

# RR1 — three encodings on the spike's own worked example  (~5 s)
python3 scratch_rr/rr1_covers_witness_probe.py
# RR1 widened — 300 positive + 150 negative real pairs      (~2 min)
python3 scratch_rr/rr1_corpus_sweep.py

# RR2 — mirror size + live boot + replay amplification      (~20 min, memory-capped)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scratch_rr/rr2_mirror_size_and_replay.py
# RR2 — the at-risk file LIST (the artifact, not a count)
cat scratch_rr/rr2_at_risk_files.json

# RR3 — full-boot completeness                              (~10 min, memory-capped)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scratch_rr/rr3_completeness_probe.py

# RR4 — find the parallelograms, then transfer              (~1 min each)
python3 scratch_rr/rr4_find_parallelogram.py
python3 scratch_rr/rr4_analogical_transfer.py     # the 2x2 grid; exit 0 iff all four cells correct
python3 scratch_rr/rr4_transfer_at_scale.py

# committed outputs, so every number above is readable without re-running:
ls scratch_rr/out/

# RR5 — regression                                          (~5 min)
git diff --stat abae030 -- runners/ domains/ substrate/ seeds/ scripts/ tests/ conftest.py  # expect: empty
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_acting_variant.py tests/test_structural_variant.py \
    tests/test_self_delta.py tests/test_gap_awareness_migrated.py \
    tests/test_self_concern_promote_migrated.py tests/test_rules_checkpoint.py \
    tests/test_persistence_migrated.py -q
# expect: 11 failed (all pre-existing, see §6), 50 passed
```

Everything under `scratch_rr/` is **measurement-only**: read-only over
`seeds/`, throwaway `Substrate` handles, imports nothing production-side
except the landed `domains/rule_signature.py` (read, never edited). No agent
logic, no seeds authored, no engine change.
