# Meta-shape arity + `CapabilityAxis` key separator — two fixes — PREREG

**Registered before any code is edited.** Worktree
`/home/matt/ocelot-meta-shape-arity-key-fixes`, branch
`meta-shape-arity-key-fixes`, detached from `main` at `cf774d3` (verified via
`git log --oneline -1 main` immediately before worktree creation; the worktree's
own `git log --oneline -1` reports the same commit).

This rung closes exactly two defects, both of which
`SHAPE_TYPE_VOCABULARY_SPIKE.md` (landed today, same commit `cf774d3`) reported
as **`[derived, not run]`** — i.e. read out of source and explicitly *not*
confirmed by running anything:

- **Bug 1** — §3.3.1: a minted `MetaShape` whose signature has *k* relations can
  only cover an observation with **exactly** *k* relations, because
  `msg_recognize`'s `Covers` guard lands on `covers_value`'s `Tuple | List` arm
  and that arm requires `pt.len() == it.len()` (`runners/dsl/src/term.rs:3754`).
- **Bug 2** — §7.2: `induce_concern`'s `CapabilityAxis` key
  (`"induced_" + "_".join(sorted(preds))`, `domains/reflective_faculty.py:1296`)
  joins snake_case predicates with the same `_` that occurs *inside* predicate
  names, so two different predicate multisets can produce one key.

Nothing else in the spike's findings is touched. In particular the spike's
larger proposals — the `ShapeRole` declaration (§5), the `scope` field (§8.3),
the uniform find-or-create on mint (§8.4) — are **out of scope** and this rung
makes no move toward them.

---

## 0. AR0 — what is already confirmed live, before this doc

Both bugs were reproduced against the **committed** engine before this document
was written. This section is evidence I already hold, not a bar; it is recorded
here so the "before" half of AR2/AR4 is not reconstructed after the fact.

**Bug 1, live** (`shape_vocabulary` + `meta_shape_growth` seeds, three
`TradeRecord` observations, the third carrying one extra attribute):

```
recognized  ms_buyer_is_a_lot_seller  [[buyer,alice],[is_a,traderecord],[lot,7],[seller,bob]]
recognized  ms_buyer_is_a_lot_seller  [[buyer,carol],[is_a,traderecord],[lot,9],[seller,dave]]
residual    None                      [[buyer,gary],[is_a,traderecord],[lot,13],[note,anything],[seller,hank]]
minted MetaShape: ms_buyer_is_a_lot_seller
  signature (('buyer',WILD), ['is_a','traderecord'], ('lot',WILD), ('seller',WILD))
```

The spike's prediction holds exactly: 4-relation shape, 5-relation observation,
no recognition. §3.3.1's own refutation test ("If it does, I am wrong") did not
refute it.

**Bug 2, live** (arithmetic only, no boot):

```
sorted(['a_b','c']) -> 'induced_a_b_c'
sorted(['a','b_c']) -> 'induced_a_b_c'      # equal: True
```

---

## 1. Scope discipline

The two bugs are **not** the same bug and must not be assumed to share a fix.
Bug 1 is a structural-coverage semantics question in Rust/graph-rule territory;
Bug 2 is a lossy string encoding in a host-layer identity computation. They are
in one rung only because they were reported by one document.

Files in scope:

- `runners/dsl/src/term.rs` (the shape-math region + the Term enum/eval),
  `runners/dsl/src/term_variants.rs`, `jsonio.rs`, `reflect.rs` — **only** if
  AR1 selects a Rust arm.
- `seeds/meta_shape_growth.json` — the `msg_*` rules' `where` clauses.
- `domains/reflective_faculty.py` — **only** the `induce_concern` key line
  (~1287-1296).
- New tests + the two docs.

Explicitly **not** touched: `domains/analogical_thinking.py`,
`domains/rule_signature.py`, `runners/dsl/src/py.rs`,
`substrate/world_adapter.py`'s checkpoint-load region (concurrent/landed
threads).

---

## 2. AR1 — Bug 1 investigation, registered before building

### 2.1 The question

`SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.3 establishes a genuine three-way trade:

> **No single container gives you WILD slots *and* residual capture *and* open
> arity.** `Set` gives residual and open arity but no WILD. `Dict` gives WILD
> and open arity but no residual. `Tuple` gives WILD and residual — and buys
> them by fixing the arity.

The meta-shape codebook demonstrably needs WILD (its minted signatures carry
WILD in the value slots — confirmed in AR0's dump above). So **"just switch to
`Set`" is a regression dressed as a fix** and is pre-registered here as a
rejected arm, not an option to be re-weighed later.

### 2.2 The arms

- **Arm A — fixed-arity discipline (§5).** Declare that a meta-shape codebook
  entry is keyed by content *and* arity, so the *k+1*-relation observation is a
  genuinely different candidate that must earn its own entry via the mint path.
  Then no engine change is needed and the only work is documenting the
  invariant and verifying the growth path actually mints the *k+1* variant
  rather than losing it.
- **Arm B — a meta-shape-grain-LOCAL open-arity coverage Term.** A new Term
  (working name `CoversOpen`) whose outer container comparison is
  sub-multiset/superset rather than equal-length, with element comparison
  delegated unchanged to `covers_value`. Used **only** by the `msg_*` rules.
  `Covers` itself and `covers_value`'s existing semantics are untouched, so
  every other caller is byte-unaffected.
- **Arm C — change `covers_value`'s `Tuple | List` arm for everyone.**
  Registered so it is on the record as considered; expected to be rejected on
  blast radius.

### 2.3 The decision rule, registered in advance

AR1 selects an arm by these tests, decided *before* writing the fix:

1. **Does Arm A's growth path actually terminate in a minted *k+1* shape?**
   Measured by running the AR0 repro with a *second* extra-attribute
   observation (recurrence ≥ 2 is `MetaShapeMint`'s own condition) and reading
   whether a second `MetaShape` is minted. If a single *k+1* observation can
   never be recognised *and* never mints, Arm A leaves it stranded — which is
   the failure the meta-shape rung exists to remove, and Arm A loses.
2. **Does the engine already have a settled precedent for relation-set
   coverage?** If the sd loop's own decode already treats a signature as a
   relation SET with existential per-relation coverage (i.e. open arity), then
   the meta-shape whole-signature `Covers` guard is the outlier and Arm B
   restores consistency rather than inventing semantics. If instead the engine
   is uniformly arity-exact at relation-set grain, Arm B is the novelty and
   carries the burden of proof.
3. **Blast radius, enumerated not characterised.** Every caller of
   `covers_value` and of the `Covers` Term (Rust callers, seed rules, Python)
   is listed by file:line in the RESULTS doc. Arm C is admissible only if that
   list is small AND every listed caller is shown to be unharmed. Otherwise
   Arm C is rejected and the RESULTS doc says so with the list attached.

**Pre-registered expectation** (so a later reader can see whether the
investigation moved me): I expect Arm B, on test 2, because
`shape_decode.rs::covers_relation` looks like per-relation existential
coverage. I have read it but have not yet enumerated the callers, and I record
here that expectation-before-measurement so agreeing evidence is not
over-credited.

### 2.4 What would make this a NO-GO

If Arm B cannot be reached without touching shared `Covers`/`covers_value`
semantics, or if the new Term's correctness cannot be established without a
larger audit than this rung should attempt, the rung reports **NO-GO with the
exact missing piece named**, per the brief. A NO-GO that names what is needed
is a complete result here.

---

## 3. AR2 — Bug 1 fix bars

**AR2.1 (headline, live).** The AR0 repro script, unchanged, prints
`recognized` for the third (5-relation) observation, with a non-null
`covered_by` naming the held 4-relation shape.

**AR2.2 (negative control, live).** An observation that genuinely matches no
held shape still reads as a residual — *not* spuriously recognised. Concretely:
after the same mint, observing an item of a different type with disjoint
predicates (e.g. `Concept{name, definition}`) must NOT be covered by
`ms_buyer_is_a_lot_seller`. Reported as the observation's `status` and
`covered_by`, live.

**AR2.3 (partial-overlap control, live).** An observation carrying only SOME of
the held shape's relations (a strict subset, e.g. `TradeRecord{buyer, lot}` with
`seller` absent) must still NOT be recognised — open arity must be
*superset*-tolerant, never *subset*-tolerant. This is the bar that separates a
correct fix from one that has simply weakened coverage.

**AR2.4 (`Covers` unchanged).** If Arm B is selected, a direct probe shows the
existing `Covers` Term still returns `false` on a length-mismatched List pair —
i.e. the shared primitive's semantics were not altered under the rug.

**AR2.5 (mint still reachable).** After the fix, an observation whose predicate
set genuinely differs from every held shape still reaches `residual` and, on
recurrence ≥ 2, still mints a new `MetaShape`. The Occam ladder must still be
able to grow; a fix that recognises everything has broken rung 4.

---

## 4. AR3 — Bug 2 investigation, registered before building

**AR3.1 — prevalence, measured not asserted.** The spike explicitly flagged
prevalence as unmeasured. This rung measures it:

- Enumerate every `induce_concern` call site in the tree and split them into
  `name_hint`-supplied (the key is authored, the join never runs) vs derived
  (the join runs).
- For every derived site whose observation is a source literal, compute the
  actual key and check the whole derived-key population for (a) a real
  collision — two different predicate multisets, one key — and (b) near
  misses: any derived-site predicate containing `_` at all, since that is the
  necessary condition for the collision to be reachable.
- Report the counts and the lists. A measured prevalence of **zero** is a
  reportable result and must be reported as such, not quietly folded into a
  justification for the fix.

**AR3.2 — existing convention, reused not invented.** Check whether the tree
already has a canonical key/identity convention for exactly this problem
(spike §7.1 lists four schemes in use: bare name, derived string join, content
hash, structural equality). The fix must reuse an existing convention if one
fits, and if it invents one, the RESULTS doc must say why none of the four fit.

**AR3.3 — literal-string readers, enumerated.** Before changing key *values*,
enumerate everything that reads a `CapabilityAxis` key / `Observation.key` /
`capability_keys` as a literal string (rule guards, Python comparisons, seed
JSON literals, captured parity fixtures, docs). The fix is admissible only if
it either (i) leaves every currently-produced key byte-identical, or (ii) the
enumerated readers are shown to be unaffected by the change. **A fix that
silently changes existing key values without this enumeration is rejected by
this prereg**, per the brief's own constraint.

---

## 5. AR4 — Bug 2 fix bars

**AR4.1 (live before/after).** The colliding pair from AR0 produces two
*different* keys after the fix, demonstrated by calling the real code path (not
a re-implementation of the join in the probe).

**AR4.2 (sized to measured risk).** The fix is the smallest change that closes
the collision while satisfying AR3.3. If AR3.1 measures zero live collisions,
the RESULTS doc says so and justifies the fix on the arithmetic (the mechanism
is certain even where the prevalence is nil) rather than on an inflated claim
about production impact.

**AR4.3 (no silent key churn).** Explicitly reported: for each currently
observed derived key, whether the fix changes its value. If any value changes,
the affected readers from AR3.3 are listed and shown to be unharmed.

---

## 6. AR5 — no regression, paired lists not counts

Per `CLAUDE.md`'s standing retraction ("**a baseline must be a list of node ids,
never a count or a characterisation**"), regression evidence is reported as
**paired before/after node-id lists** from the *same* command, in the *same*
environment, run in this worktree:

- `cargo test` for the Rust shape-math region (`term.rs` / `shape_decode.rs`
  unit tests) — before and after, with the failing test names listed.
- The Python suites that cover the two grains, identified by search rather than
  assumed:
  `tests/test_meta_shape_first_class_migrated.py` (the meta-shape rung's own
  gate), the `induce_concern`/`CapabilityAxis` suites the Pattern-C rung used
  (`tests/test_axis_mint_novelty.py` and the shape-decode-loop migrated
  suites), and `tests/test_composer_driver_migrated.py` (which holds the
  captured `induce_concern` parity fixture, and is therefore the suite most
  likely to catch an unintended key-value change).
- Every one of those is run **before** any edit in this worktree and **after**,
  and both node-id lists appear in the RESULTS doc. A test that was already red
  at `cf774d3` is named as such; a test that turns red is a blocker, not a
  footnote.

New gates added by this rung (registered here so they cannot be invented to fit
the outcome afterwards):

- A Rust unit test for the new coverage semantics (if Arm B): superset accepted,
  subset rejected, disjoint rejected, WILD honoured, and the *existing* `Covers`
  behaviour asserted unchanged in the same file.
- A Python gate reproducing AR2.1 + AR2.2 + AR2.3 end-to-end through the seeds.
- A Python gate for AR4.1.

---

## 7. What this rung will NOT claim

- It will not claim the container trade of §3.3 is dissolved. If Arm B lands,
  the honest statement is narrower and will be written as such in RESULTS.
- It will not claim Bug 2 had production consequence unless AR3.1 measures one.
- It will not extend either fix to the other shape-bearing grains
  (`ShapeSignature`, chunk entries, stroke quanta, `SpaceQuantum`). Whether they
  want the same semantics is a separate, unmeasured question and will be left
  named-not-built.
