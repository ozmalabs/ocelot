# `run_rules` RETURNED OVER UNSETTLED STATE — A GENUINE ENGINE BUG, FOUND, REPRODUCED, FIXED, AND BOUNDED

*Pre-registration `VISION_FIXPOINT_SETTLE_PREREG.md`, committed BEFORE any
headline at **`1430d7d6`**.*

| | |
|---|---|
| **Branch ACTUALLY in use** | **`worktree-agent-ad325918cc2ff96ac`** — NOT the intended `gamma-substrate/fixpoint-settle`. Auto-generated worktree name, as the last ten rungs had. |
| Base SHA | `e8bf398747c4b14f54a8519d234b0667f246438a` |
| Prereg commit | `1430d7d6` |
| Reproduction (fails) | `64d57c92` |
| The fix | `1ebd1450` |
| Gate + positive control | `9f1741a2` |
| Discriminator | `5ea6eb36` |
| **Engine** | **`682b5e891408`** — this worktree's OWN build (`scripts/engine_build.sh`), provenance reads `own`. THIS RUNG ADDS RUST. |
| Pre-fix probe engine | `bfb2dbafed8f` (built only to prove the gate can fail; discarded) |
| **Seeds drawn** | **0** — measured, not assumed: `scripts/seed_audit.py --check 85000 85999` → `{"ok": true, "outside": []}`; 0 unknown sinks, 0 parse errors. **85000–85999 entirely CLEAN.** |

---

## 1. THE VERDICT, DECIDED FIRST: IT IS A BUG, NOT A SPECIFICATION

The pre-registration made this the first question precisely so that "it
surprised two competent authors" could not stand in for a defect. The contract
is unambiguous, and it is written on the function itself
(`substrate.rs`, `run_rules`):

> *"The committed **fixpoint** runner. UNCHANGED SEMANTICS — **runs to an exact
> fixed point** (or the cap), exactly as every seed has always seen it."*

Corroborating, and all in the same direction:

- `run_rules_opts`'s own doc: *"A run that currently ends on no-progress is a
  **TRUE fixed point** (period 1)."* That sentence is the defect stated as an
  assumption — the engine treated "no rule reported progress" as *proof of* a
  fixed point, when it is only evidence of one.
- `CLAUDE.md`: *"the `run_rules` fixpoint IS the decode → grow → re-decode
  loop."*
- The loop's structure: `run_rules_opts` is a `while steps < max_steps` loop
  with a no-dirty fast exit and a `!any_progress` exit. **It is not one pass.**

**So the engine was wrong, and the seeds relying on multi-pass convergence were
right to.** The two rungs' workarounds — the motion rung's `mflood` phase flag
and the cut-mint rung's install-between-the-halves — were correct engineering
against a defective scheduler, not misuse of a documented one-pass API.

**A correction to the brief, recorded rather than absorbed:** the cut-mint
rung's "schedules every dirty rule in ONE PASS WITH NO BREAK" is accurate
*per pass*, but on its own it is **not** a fixpoint defect — the outer loop
does iterate, and a rule that misses its cue in pass *n* should fire in pass
*n+1*. The observation only becomes a defect in combination with the second
mechanism below. The supervisor's unification was **right**, but not for the
reason either report gave.

## 2. THE SUPERVISOR'S LEAD WAS WRONG, AND THE ENGINE HAD ALREADY NAMED THE RIGHT ONE

Registered in the prereg before measuring: the offered lead — *"a rule with a
**stale-but-valid cursor** enumerates zero"* — is **not** what the code shows.
The cursor in the failing case is **valid and correct**; the enumeration is
empty because the *driving edges are stable*. Different condition, same
symptom. Reported as a wrong lead, per §7.

The engine had already named the real one, in its own `SUBSTRATE_TRACE_RULE`
output inside `try_incremental_match`:

> `*** ALL ZERO: no new driving edges -> nothing scanned -> rule CANNOT fire this pass even if its where is now true (the stable-edge attr-gated bug) ***`

`try_incremental_match` is semi-naive: it enumerates bindings driven **only by
edges new since the rule's cursor**. A rule whose match-edges are stable
enumerates **zero** — while `rule_cost_count` still increments, exactly the
locality rung's *"an enumeration count is not a scan count."*

**But that alone is not the bug**, and this is the finding that most changes
the risk model — see §4.

## 3. THE PRECISE CONDITION — A THREE-RULE INTRA-PASS RACE

`dirty_by_writeset` (`substrate.rs` ~527) already mitigates the bare
stable-edge story: when a firing rule's `write_set` meets a consumer's
`read_set` on an `Attr` key and the consumer has a where-clause, it dirties the
consumer **and clears its cursor**, forcing a full re-match. The read-set
walker (`collect_term_reads`) is an exhaustive match with no catch-all, so
every *statically visible* attr key in a where-clause lands in `read_set`.
**The mitigation works.**

What leaked was a single line — the early-out at `substrate.rs:540`:

```rust
for j in 0..self.rules.len() {
    if self.rule_dirty[j] { continue; }   // <-- returns BEFORE the cursor clear
```

**Dirtying a consumer and invalidating its cursor are two DISTINCT
obligations. The early-out discharged only the first.** The exact sequence:

1. **`P_edge` fires**, writing an edge type in consumer `B`'s read-set. `B` is
   dirtied; `attr_flip` is false, so its cursor is **correctly left intact** —
   new edges drive the rescan, nothing is missed.
2. **`A` fires LATER IN THE SAME PASS**, writing attr `K` that `B`'s
   where-clause reads. `B` is **already dirty**, so the `continue` fires and
   **`B`'s cursor is never cleared.**
3. **`B` is tried** on the incremental path with a *valid* cursor and **zero**
   new driving edges. It enumerates nothing and cannot observe the attribute
   flip on its stable edges.
4. Every rule reports no progress → `!any_progress` → **`run_rules` returns
   declaring a fixed point over a graph that has not settled.**

It is bounded because `to_try`'s dirty bits are all cleared at pass top, so a
consumer that is *clean* at pass start always gets its cursor cleared. **The
race requires a third rule** to make it already-dirty first.

### 3.1 The reproduction — three rules, five nodes

`substrate.rs::run_rules_returns_over_unsettled_state_when_attr_write_follows_structural_dirty`
and, through the shipped engine,
`tests/test_fixpoint_settle_migrated.py`.

```
chain:  s1 -[step]-> s2 -[step]-> s3
gate:   s3 -[gate]-> n1
link:   n1 -[link]-> n2                      (STABLE — never added to)

fs_churn     : ?a -[step]-> ?b  where ?a.on == 1  => ?b.on = 1 ; add ?b -[tag]-> ?b
fs_open_gate : ?p -[gate]-> ?q  where ?p.on == 1  => ?q.go = 1
fs_consume   : ?x -[link]-> ?y  where ?x.go == 1 && |tag(?x)| == 0  => mint Marker
```

**Result on the pre-fix engine:** `run_rules(1000)` returns **3 steps**; a
second `run_rules` makes **0 further steps**; `n1.go == 1.0` (so `fs_consume`'s
where-clause is genuinely TRUE); **0 Markers minted, 1 expected.** A fixed
point that is not a fixed point.

### 3.2 Discrimination BY INTERVENTION, not by inference from outcome

The prereg required this: *"An outcome consistent with two mechanisms
discriminates neither."* Three controls, each isolating one variable:

| Control | Result | What it rules out |
|---|---|---|
| **R2** — identical graph, identical rules, `go=1` present **before** the first pass | **settles, 1 Marker** | the rule set, the where-clause, and the graph shape. Only the *scheduling of the attr write* differs. Reproduces the motion rung's own fix. |
| **Two-rule arm** — `fs_churn` removed | **settles even PRE-FIX (VERIFIED on engine `bfb2dbafed8f`: only the `[False]` arm reddens; this arm stays green)** | the bare stable-edge story. The mitigation genuinely closes it; the third rule is **required**. |
| **Remove line 540's `continue`, change nothing else** | reproduction **goes green** | every other candidate mechanism. |

That last row is the decisive one: the defect is fixed by intervening on the
exact line the mechanism names.

**Candidates the prereg listed, and their disposition:** (i) match set created
by another rule in the same pass — *not it, the outer loop handles that*;
(ii) batch application showing pre-pass state — *not it, unrelated code path*;
(iii) **stale cursors — NOT IT** (the cursor is valid; the supervisor's lead
was wrong); (iv) dirty-bit propagation missing an edge type — *not it, the bit
IS set*; (v) **the stable-edge attr-gated path with a `dirty_by_writeset` miss
— THIS, and specifically via the already-dirty early-out.**

## 4. BLAST RADIUS — ENUMERATED, AND IT INVERTS THE BRIEF'S RISK MODEL

Static enumeration over **761 seed JSON files** (`seeds/` + `code_authoring`,
`expansions`, `generated`, `procedural`, `self_authored`), **0 parse
failures**, by structural `json.load` + AST walk — **never substring
selectors** (§12). Of 1942 rule entries, **768 are loadable engine rules** (the
rest are `head`/`body` knowledge entries with no `match`+`effects`).

**1824 ordered pairs (A, B)** exist where A writes attr `K` and B's
where-clause reads `K`:

| Bucket | Pairs |
|---|---|
| STABLE-EDGE (no same-seed rule adds an edge B matches on) | **916** — 255 distinct consumers, 66 seeds |
| EDGE-DRIVEN (order-robust by construction) | **308** |
| UNDETERMINED (edge-adder only cross-seed; `depends_on` closure unresolved) | **515** |
| IMMUNE (engine forces full re-match: `batch`, `reads_external`, repeated edge-type, `reads_any`/`writes_any`) | **85** |

**The 916 STABLE-EDGE pairs are NOT the exposure.** Because
`collect_term_reads` is exhaustive and `dirty_by_writeset` clears the cursor
whenever `hits_attr && has_where`, the mitigation covers all of them. Reporting
916 as the blast radius would have been a large, plausible, **wrong** number —
and it is the number the brief's framing predicts.

**The actual exposure is the race-constructible subset: 316 pairs across 95
distinct consumers**, requiring a third rule whose *structural* write lands on
the consumer earlier in the same pass:

| Seed | Race-constructible pairs |
|---|---|
| `impasse_escalation` | 41 |
| `shape_decode_loop` | 34 |
| `goal_derivation` | 23 |
| `vision_floor` | 21 |
| `nav_intent` | 20 |
| `grid_navigation` | 16 |
| `meaning_inference` | 15 |
| `question_driving` | 15 |
| *(87 further seeds)* | remainder |

`shape_decode_loop` is the structurally purest case and the one the
architecture leans on hardest: **all 17 rules match on the single `observed`
edge**, and the entire growth ladder coordinates through node attrs (`status`,
`residual`, `gen_checked`, `dim_checked`, `transform_explained`,
`codebook_epoch`). No rule mints `observed` edges, so every rung depends on a
full re-match.

**316 is an upper bound on CONSTRUCTIBILITY, not a count of observed
breakage** (§8). Whether the race actually fires depends on rule index order
and pass composition, which the static walk does not model. **Naming the
exposure is the deliverable; I did not re-litigate the landed rungs.**

### 4.1 Stated limits on the enumeration — an enumeration with unstated blind spots is worthless

1. **Python-installed rules are entirely outside the scan.** Only seed JSON was
   walked. Rules built by `domains/*.py` Term/rule builders are unenumerated.
2. **Dynamic attr keys are not enumerable.** `AttrByName` sets `reads_any`,
   which is conservative (always dirtied + cursor cleared) — so it is *safe*,
   but invisible to a key-level analysis.
3. **Term-tree indirection.** `ShapeDecode`, `GenInfer`, `UseTool`, `Holds`
   compute values whose graph effects were not modelled; only static reads
   counted.
4. **Cross-seed pairing genuinely undetermined (515 pairs).** `depends_on`
   closures were not resolved, so co-loading is unknown. Bucketed separately
   rather than guessed.
5. **Rule ordering within a pass was not modelled.**

## 5. THE INSTRUMENT IS ALIVE — POSITIVE-CONTROLLED, BOTH LIMBS

`assert_settled` fired once and then discarded **0 of 160** runs. That is
exactly the shape of a check that has stopped being able to fire, and the
standing rule is that *a gate that has never been ABLE to fail has not been
tested*. Controlled directly:

| Control | Result |
|---|---|
| **P1a** — plant a cell retaining an admissible neighbour with a **smaller label** | **RED** (`unsettled_pairs > 0`) |
| **P1b** — plant a cell the tolerance broadcast **missed** (`mtol_done = 0`) | **RED** (`cells_without_tolerance > 0`) |
| **P2** — a genuinely settled field | **GREEN** |

P2 is load-bearing: without it, a check that always returned red would have
"passed" both positive controls.

**Verdict: `assert_settled` is NOT a dead instrument. The motion rung's
0-of-160 is a real zero**, and the numbers resting on it stand.

### 5.1 MY OWN GATE IS ALSO POSITIVE-CONTROLLED

The same standard applied reflexively. The engine was rebuilt with the fix
reverted (engine `bfb2dbafed8f`): the `[False]` arm **reddens** (0 Markers with
`go=1.0` present) while the `[True]` control arm **stays green** — the gate
discriminates the defect, not the harness. Fix restored, engine back to
`682b5e891408`, Rust tree verified clean.

## 6. THE FIX, AND WHAT IT MOVED

One line removed. The dirty bit is idempotent, so running the intersection
unconditionally is correct; the cost is the `read_set` intersection for
consumers already scheduled. `mark_node_mutation`'s blanket cursor-clear was
always the stronger guarantee — this brings the rule-effect path in line with
it.

| Gate | Result |
|---|---|
| **Vision bench oracle, WITH `data/`** | **222 passed** — exactly the oracle |
| Rust lib suite | **616 passed / 0 failed** |
| Provenance + endpoint guard | **641 passed** |
| This rung's gate | **6 passed** |
| **Targeted regression on the EXPOSED seeds** | **149 passed** — sdloop-vision · dimension-inference · transform-decode · composer-driver · meaning-inference · quanta-navigation · ink-decode · gap-awareness |

**The full `-k migrated` bench was NOT run to completion, and I report that
rather than implying coverage I do not have.** It was started, ran ~35 minutes
to 9%, and was projecting ~6 hours (the protocol's prior record is ~48 min; the
difference is most likely the `data/` symlink pulling in the vision corpus).
I stopped it and ran the **targeted** subset above instead — the seeds the
blast radius actually names, which is where a scheduling fix could plausibly
change behaviour. That is a deliberate substitution of a *targeted* regression
for an *exhaustive* one, and it is a real gap in coverage: **a regression in an
unexposed, unrun seed would not have been caught.**

**The oracle did not move.** An engine-level scheduling change that alters when
cursors are cleared, and the entire vision bench is byte-stable. Read
honestly, that means the 222-test bench **never exercised the race** — it is
evidence the fix is safe, and *not* evidence the bug was harmless.

## 7. AN INCIDENTAL UNBLOCK, REPORTED BECAUSE IT AFFECTS FUTURE RUNGS

`VISION_PROTOCOL.md` records **twice** that `cargo test` cannot link this crate
(pyo3 `extension-module` ⇒ undefined libpython symbols), and rungs have been
routing around it by gating through Python. It links fine with:

```
RUSTFLAGS="-L /usr/lib -l python3.14" cargo test --release --lib
```

**616 lib unit tests run in 0.45s.** No file changed; it is a flag. Rust unit
tests are available to this tree again. (Path is this machine's
`sysconfig` `LIBDIR`/`LDLIBRARY`; not portable as written.)

## 8. BOUNDS

- The reproduction bounds **the condition**, not its **frequency in the wild**.
  It is a constructed three-rule case, not a sampled one.
- **316 race-constructible pairs is an upper bound on constructibility**, not a
  count of demonstrated breakage. Confirming any individual pair requires
  running the engine on that seed, which this rung did not do.
- The enumeration covers **seed JSON only** — Python-installed rules are a real
  and unmeasured blind spot (§4.1).
- The 222-test oracle being unmoved bounds **regression risk**, not the bug's
  historical impact. No landed number was re-run under the fix, so **no claim
  is made here about whether any published result changes.**
- `assert_settled`'s positive control validates **that instrument**, on the
  motion field. It says nothing about the other 27 counters the term-eval rung
  found BLIND or INERT.

## 9. WHAT I GOT WRONG

1. **I initially expected the 916 STABLE-EDGE pairs to be the blast radius.**
   They are not; the mitigation covers them. The correction came from reading
   `collect_term_reads` and `dirty_by_writeset` properly rather than from the
   symptom, and it cut the reported exposure by ~3× while making it *specific*.
   Had I shipped 916, it would have been a confident, plausible, wrong number.
2. **I accepted the supervisor's unification before verifying it.** It happens
   to hold, but the cut-mint observation as *stated* ("one pass, no break") is
   not a fixpoint defect on its own — the outer loop iterates. Right answer,
   wrong stated reason, and I nearly propagated the wrong reason.
3. **The first reproduction attempt was a Rust unit test in a crate whose tests
   cannot link.** I nearly recorded the pre-existing blocker as a limitation
   (as two prior rungs did) instead of spending five minutes to defeat it.
