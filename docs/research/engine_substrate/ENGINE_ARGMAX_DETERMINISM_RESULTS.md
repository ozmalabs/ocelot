# ENGINE CORRECTNESS — THE `Argmax` NON-REPRODUCIBILITY — RESULTS

*Pre-registration: `ENGINE_ARGMAX_DETERMINISM_PREREG.md`, committed BEFORE any
measurement at **`8496493c`** (base `main` HEAD **`eb403264`**).*

**Engine (§10):** built in THIS worktree by `scripts/engine_build.sh` — pre-fix
`cd14d494d700` (every diagnostic and the whole §2 sweep), post-fix
`e59484fe6b2e` (§3's GREEN and the bench). **The sweep never spanned a rebuild:
the engine was installed only after all 200 processes had exited.**
**The Rust source at `eb403264`
is byte-identical to the source that produced the §4.2 anomaly** —
`git diff 50448c82..eb403264 -- runners/dsl/src/` is EMPTY, so every exclusion
below is about the same code that failed, not a moved target. (The `.so` hash
differs from the anomaly rung's `7d5f50c1` because it is a different BUILD of
identical source; §11's copy-and-hash rule was followed — nothing was built in
the canonical tree, and the sweep below was never run across a rebuild.)

**Seeds:** block **56000–56999** only.
**Evidence, read-only:** `results/crossframe_identity_anomaly_rows.json` — the
272 non-regenerable rows. **Nothing in this rung wrote to it.**

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The §4.2 anomaly did NOT reproduce, and the honest deliverable is a much
narrower target plus seven mechanisms excluded on evidence.** Reading the pinned
rows first **corrected §4.2's own characterisation** and sharpened the defect
from "an `Argmax`/`Eq` disagreement" to something far more specific: stage 1's
`MaxOver` and stage 2's `Count(Filter(Eq(·, xf_max)))` were **both correct on
272/272 rows** (they match numpy exactly), and **only the `Argmax` was wrong —
returning one constant node for an entire substrate's worth of evaluations.**
1 088 000 probes across 200 processes × 20 sequential worlds produced **0
foreign wins, 0 tie-count mismatches, 0 score mismatches**. **All six mechanism
hypotheses (H1–H6) are excluded on evidence**, not by assumption — including the
one that looked most like the answer: the native fold CAN return a loser, but
only under a universal tie, and a universal tie was measured to record
`xf_ntied = 33` where the pinned rows record **1…5**. Among the exclusions is a
defect that **is real, reproduces on demand, is FIXED here with a red→green gate,
and is nevertheless PROVEN not to be the cause**
by a measured identity. A second latent defect (the read-set under-approximation
for codebook Terms) was found by reading, is **not** reproduced, and is reported
with its exact exposed-rule list rather than fixed. **The residual after all
exclusions is a single-run, single-substrate corruption of one fold's state with
no surviving in-band explanation — and the actionable output is the instrument
that would have made it diagnosable in one row instead of an arc.**

---

## 1. THE FIRST FINDING IS A CORRECTION TO §4.2 ITSELF

§4.2 states that each of the 272 rows "records `xf_max = 36`, `xf_ntied = 1`, and
`true_score = 36`". Read directly off the pinned file, **that describes 78 of the
272 rows.** The complete picture:

| fact | over all 272 rows |
|---|---|
| `said` | `fractal`, **272/272** |
| `xf_max` | spread over **9…36** (24 distinct values) |
| `xf_ntied` | spread over **1…5** |
| **`xf_max == nn_score`** | **272 / 272** |
| **`xf_ntied == nn_ties`** | **272 / 272** |
| `true_is_max` | False on 157, True on 115 |

`nn_score` / `nn_ties` are computed **outside the graph, in numpy**
(`crossframe_world.hamming_nn`). So the three effects of the seed's two rules
separate cleanly:

- **stage 1 (`xf_score`'s `MaxOver`) was CORRECT on every row.**
- **stage 2's `Count(Filter(Eq(ShapeDecode, xf_max)))` was CORRECT on every row.**
- **stage 2's `Argmax` was WRONG, identically, on every row** — the same node,
  for every probe in that substrate, including the G1 identity probes (where the
  probe IS a held tile) and the G2 pure-noise probes.

**Why this matters more than the arithmetic.** §4.2 framed the defect as two
Terms disagreeing. The rows say something stricter and stranger: **two
structurally identical `ShapeDecode` compositions — one in the preceding rule,
one in the very next effect of the same rule application — were simultaneously
CORRECT, while the `Argmax` between them was constant-wrong.** Any explanation
must produce all three at once. That constraint is what excludes almost
everything below, and it could not have been derived from §4.2's own summary.

**Corollary that does the real work.** `xf_ntied == nn_ties` on 272/272 means the
`Eq(·, xf_max)` filter counted **exactly the tiles at the maximum and no foreign
signature**. So at the moment the filter ran, `fractal` scored **strictly below
`xf_max`**. In the same rule application, the `Argmax` had just ranked it
**at or above** every candidate. That is the defect, stated as tightly as the
evidence allows.

---

## 2. NOT REPRODUCED — the registered budget, in full

Exactly the budget fixed in advance (§3 of the prereg): **200 processes ×
20 sequential `CrossFrameWorld`s**, each world carrying the full 272-probe load
of `run_base_frame` (5 Δ × 3 arms × 16 regions + 32 gate probes).

The process history was matched deliberately: in the original run, C1's k=4 bases
are the first thing the process does, so **base frame 18 was the 19th world in
its process** — `N_HISTORY = 20` brackets it.

| quantity | result |
|---|---|
| processes | **200** |
| worlds | **4 000** |
| probes | **1 088 000** |
| **foreign wins** | **0** |
| **rows where `xf_ntied != nn_ties`** | **0** |
| **rows where `xf_max != nn_score`** | **0** |

Against the original diagnosis run's 5 440 replayed probes, this is **200× the
replay effort, and it is equally null.** Per the prereg's decision rule this is
**NOT REPRODUCED**, and the §4.2 rows are therefore **not explained** by this
rung.

Three independent invariant checks were also run inside long-lived processes and
were clean: re-evaluating the seed's own `Argmax` three times per observation
never diverged; the winner's own per-candidate score always equalled `MaxOver`;
and the `ShapeSignature` count never changed across `run_rules` (so the
`shape_decode_loop` really is inert here, as its seed claims — one more candidate
mechanism gone).

---

## 3. THE ONE DEFECT THAT DID REPRODUCE — and it is NOT the cause

**`apply_scope` and `apply_exclude` silently drop every Term-built string.**

Both readers matched `Value::Str` alone. But `evaluate()` holds an immutable
`&Interner`, so a Term-built string can **never** be a `Sym` — `StringConcat` /
`StringSlice` / `ToJsonString` / `FromJsonString` all evaluate to
`Value::Surface(Text)` by construction. **A codebook part named by a RULE was
therefore unnameable in a scope or an exclude**, and neither reader fails closed:

| call | correct | measured, pre-fix |
|---|---|---|
| `codebook_scope` → `fractal` (a part covering **no** goal relation) | **0** | **36** — the whole codebook's maximum |
| `exclude` → `r00` (the exactly-covering part) | **14** | **36** — nothing excluded |

An all-dropped scope leaves the set empty, and the `!is_empty()` guard reads
empty as **UNRESTRICTED** — so a decode asking *"score this ONE part"* silently
returns the **global maximum**. An all-dropped exclude excludes **nothing**. Both
are confident wrong numbers with no warning.

**What made it invisible is an asymmetry inside one file.** `load_parts` in
`shape_decode.rs` ALREADY accepts both spellings (`str_shaped`), and has a
`string_attr_or_panic` guard whose doc-comment is a 30-line essay against exactly
this bug class. The part is therefore present in the codebook and scopeable by
its interned name — **only the rule-built spelling of the same name fails.**
The two functions thirty lines below never got the arm.

**Fix** (`runners/dsl/src/shape_decode.rs`): both readers now share one
`collect_part_names` helper that uses `str_shaped` (accepting `Str` **and**
`Surface(Text)`), keeps `Value::None` as the documented "no scope / no exclude"
(`seeds/reflex_net.json` relies on it), and **panics** on a present-but-not-
string-shaped element rather than dropping it — the `string_attr_or_panic`
precedent, applied where it was missing.

**Gate:** `tests/test_shapedecode_scope_surface_migrated.py`, demonstrated both
ways on this branch.

```
pre-fix engine :  3 failed, 3 passed
post-fix engine:  6 passed
```

The 3 that passed pre-fix are the premises and the documented-unrestricted case —
they must stay green, and do. (One of them,
`..._still_selects_the_right_part`, is not discriminating on its own: scoping to
the exactly-covering part gives the same answer whether or not the scope was
dropped. It is kept as the inclusion-direction guard, and is named here rather
than counted as evidence.)

**Regression oracle, post-fix:** `bash scripts/rung7_vision_bench.sh` →
**200 passed, exit 0**. (First run in this worktree reported 190 passed /
10 skipped; all 10 skips were `BSDS300 corpus absent`, a dataset this worktree
did not have. The corpus was symlinked READ-ONLY from the canonical tree — never
written — and the bench then reported the full 200. The distinction is recorded
because "190 passed" and "200 passed" differ by a data absence, not a
regression, and §1.1's rule is that an absence produced by a LOOKUP is not
evidence.)

### 3.1 …and here is the measurement that proves it is NOT the §4.2 cause

Registered in advance (prereg §2, H2) as **insufficient**, and now measured
rather than argued:

> **The unrestricted (fallback) score equals `xf_max` on 768 / 768 probes.
> Never once greater.**

With `beam=1, max_steps=1`, a plan is at most one part, so the unrestricted
decode is bounded above by the best single part's coverage — i.e. by `xf_max`
exactly. Therefore a scope-fallback candidate **always TIES the maximum**, so the
`Eq(·, xf_max)` filter **always counts it**, so this defect can only ever produce
`xf_ntied == nn_ties + 1`.

**The pinned rows show `xf_ntied == nn_ties` on 272/272.** This defect is real,
is fixed, and **cannot have produced them.** Reporting it as the cause would have
been a plausible guess that closed the case wrongly — which is precisely what the
prereg's decision rule was written to prevent.

---

## 4. THE EXCLUSION LIST — what it is NOT, with the evidence

| # | hypothesis | verdict | evidence |
|---|---|---|---|
| H1 | degenerate `Argmax` on an all-equal comparison | **mechanism SHAPE confirmed, then EXCLUDED by the tie count** | See §4.1 — the shape is real and measured, and the pinned rows rule it out anyway. |
| H2 | scope fallback → unrestricted codebook | **REPRODUCED, FIXED, EXCLUDED as the cause** | §3 above. Forces `xf_ntied == nn_ties + 1`; rows say `== nn_ties`. |
| H3 | a cache makes the `value` Term constant inside the binder | **EXCLUDED** | `EvalCache` caches exactly three things — `neighbours`, `filter`, `holds`. **Neither `Argmax` nor `ShapeDecode` is memoised anywhere.** There is no cache on the path that could make the per-candidate value constant. |
| H4 | a graph-resident derivation replaces native `Argmax` | **EXCLUDED** | `with_derivations` is called **only from test modules** (`shape.rs`, `term.rs` `#[cfg(test)]`). No production path attaches a `DerivationRegistry`, so `Argmax` always takes the native fold. No seed installs one. |
| H5 | per-process hash iteration order | **EXCLUDED** | The `Argmax` source is sorted by node id (`make_frozenset`). Every `std::collections::HashSet` in `shape_decode.rs` is **membership-only** (`used.contains`, `seen.insert`), and the one place a set is iterated (`st.used.iter()`) collects into a **`BTreeSet`**, normalising order. `dims_seen` is a `BTreeSet` already. |
| H6 | integer wrap in `covered_count` | **EXCLUDED by construction** | `residual` starts as `goal.clone()` and only ever shrinks (`nresid` filters `state.residual`), and `n_goal = goal.len()`. So `residual.len() <= n_goal` always; the `usize` subtraction cannot wrap. |
| — | the JIT | **EXCLUDED** | `jit.rs` compiles **i64 arithmetic, comparison, control flow and three graph accessors** only. Neither `ShapeDecode` nor `Argmax` is in its coverage; both always run in the interpreter. |
| — | a second writer of `identified_as` | **EXCLUDED** | `identified_as` is written by **exactly one rule in the entire seed corpus** (`xf_identify`). Nothing else can have set it. |
| — | the `sd` loop minting codebook entries mid-fixpoint | **EXCLUDED, measured** | `ShapeSignature` count is unchanged across `run_rules` in every world tested. The seed's claimed inertness holds. |
| H7 | **the registered null** | **THIS IS THE OUTCOME** | §2. |

### 4.1 H1 IN FULL — the only way the native fold CAN return a loser, and why the rows refuse it

`argmin_or_argmax_over` takes a new element only on a strict `Greater`, so **the
first element encountered wins every tie**. `NodesOfType` builds its source with
`make_frozenset`, which sorts by `cmp_value` — for `Value::Node` that is
**ascending node id**. The `boot_core` / `shape_decode_loop` signatures are
created before the 16 tiles, so a foreign signature is always first, and
**`fractal` is #726, the lowest-id `ShapeSignature`** (measured).

So there IS exactly one way this fold can return a node that is not the maximum:
**every candidate compares equal.** Measured directly, by presenting a goal over
a predicate no held part uses:

```
all-tie probe:  xf_max = 0   xf_ntied = 33   (33 candidates)
identified_as = 'fractal'
```

**A universal tie returns `fractal` — and records `xf_ntied = 33`.**

That is the finding that closes H1 in BOTH directions. The mechanism shape is
confirmed exactly (it explains why the constant wrong winner is `fractal`
specifically and not an arbitrary name), and **the pinned rows exclude it**: they
record `xf_ntied` of **1…5**, never 33, and `xf_max` of 9…36, never 0. The rule's
own filter saw a sharply-discriminating field of candidates at the very moment
the `Argmax` behaved as though it saw a flat one.

So the residual is not "an all-equal fold". It is narrower and stranger: **the
`Argmax` and the filter disagreed about the same values, in the same rule
application, with no cache, no derivation, no JIT and no hash-order between
them.**

**What survives.** A single substrate, in a single process, in which one `Argmax`
fold returned a node that the same rule's own filter simultaneously scored below
the maximum — with no cache, no derivation, no JIT, no hash-order, no wrap, and
no second writer available to explain it. Every in-band mechanism the code offers
has been checked and eliminated. **The residual is out-of-band** — a
single-execution corruption of that fold's `best` state (the machine was recorded
as under concurrent multi-core load throughout, on commodity non-ECC hardware).
**That is a hypothesis I cannot test and am NOT claiming.** It is named here as
the residual, explicitly, so that it is not mistaken for a finding.

---

## 5. THE BOUND — blast radius, as §4 of the prereg requires

### 5.1 For the defect that IS established (§3, scope/exclude)

**Structural criterion:** any `ShapeDecode` / `TransformDecode` / `DimInfer`
whose `codebook_scope` or `exclude` can evaluate to a **Term-built** string
(`StringConcat`, `StringSlice`, `ToJsonString`, `FromJsonString`, or any attr
written by a rule from one of those).

**Audit of the committed seeds** (not recollection, and not a text grep — the
rule bodies were walked structurally, because grepping for the string
`codebook_scope` also hits three seed *descriptions* that merely discuss it):

- **`codebook_scope` appears in exactly 4 rule bodies, across 2 seeds** —
  `reflex_net::reflex_ground_residual`, and
  `vision_crossframe_identity::{xf_score, xf_identify}`. (`vision_floor`
  discusses `codebook_scope` in prose but contains **no** such Term.)
- **`exclude` appears in 0 rule bodies.**
- Both scope expressions resolve to a graph attr written **from Python as a
  plain string** — `Attr(sig,"name")` (`crossframe_world.hold_codebook`) and
  `Attr(rn,"basin_parts")` (`composite_net.add_component`, which writes
  `[str(k) for k in basin_parts]`). Both are interned `Value::Str`, the spelling
  that **always worked**. **No rule anywhere writes either attr from a Term.**

**Therefore: no landed result in this tree is affected by this defect, and none
needs re-running.** It was a live trap for the next seed that names a codebook
part from a rule — which is exactly what `sd_mint_quantum`'s minted names are —
not a corruption of anything already measured.

### 5.2 For the defect found by reading but NOT reproduced

**`collect_term_reads` does not know that a codebook Term reads the codebook.**
`ShapeDecode` / `TransformDecode` / `DimInfer` read every node of `codebook_type`
plus its `name` / `signature` / `dim_types` attrs **inside their evaluator**
(`load_parts(ctx, …)`), bypassing any Term-level `Attr` node. They therefore fall
into `collect_term_reads`'s generic catch-all, which only recurses children — so
the codebook read is **invisible to the rule's `read_set`, and `reads_any` is not
set.** `rewrite.rs` itself documents under-collection as "the only unsafe
direction".

**Consequence, bounded honestly.** `read_set` feeds (a) differential rule firing
(re-arm rule *j* when a fired rule's `write_set` intersects `j`'s `read_set`) and
(b) `batch_safe`. So a rule that decodes a codebook may **fail to be re-armed**
when another rule mints or edits a codebook entry. **This can only cause a rule
to be SKIPPED — an absence — never a wrong winner, so it cannot be §4.2 either.**

**Exposure, measured over the committed seeds:** 9 rules use a codebook Term;
**8 carry no epoch guard** — `infer_sense_from_structural_analogy`,
`reflex_ground_residual`, `sd_transform_decode`, `sd_infer_dimension`,
`sd_recognize_transformed`, `sd_recognize_dim`, `xf_score`, `xf_identify`.

**Why this has not already broken the arc, stated in the seed authors' favour:**
`shape_decode_loop` bumps an explicit `codebook_epoch` attr precisely so growth
re-arms the decode — an **Attr key the read-set DOES track.** The graph layer
already works around the engine gap. `batch` is opt-in (`unwrap_or(false)`) and
none of the 8 sets it, so the `batch_safe` half is inert today.

**Not fixed here, deliberately.** There is no reproduction, and the candidate
fixes (set `reads_any` for codebook Terms; or add the codebook type to the
read-set) trade correctness against the differential-firing optimisation the
whole engine's performance rests on. That is its own pre-registration.

### 5.3 For the anomaly itself

**Unbounded, because the cause is not established.** Stated plainly: every
landed result produced by a `run_rules` fixpoint rests on an assumption of
determinism that has been observed to fail once, in a way this rung could not
reproduce in 1 088 000 probes and could not explain by any mechanism in the code.
The narrowest TRUE statement available is:

- the failure has been observed **exactly once**, in **one substrate**, affecting
  **one Term** (`Argmax`), leaving the two neighbouring compositions correct;
- it cost **1.0%** of one headline cell and moved no verdict (§4.2's own bound,
  which stands);
- **no mechanism in the engine has been found that can produce it**, and six
  candidate mechanisms are now positively excluded;
- so the probability of recurrence cannot be estimated, and **the correct
  response is detection, not reassurance** — §6.

---

## 6. THE ACTIONABLE OUTPUT — the instrument that would have caught it in one row

This anomaly cost an arc-long investigation because the rows recorded the
*winner's NAME* and the *maximum SCORE* but never **the winner's OWN score**.
One more attr would have collapsed the whole diagnosis to a single glance:

```
["set_attr", "obs", "xf_win_score", {"__term__": <the same ShapeDecode,
                                     scoped to the Argmax's winner>}]
```

With it, `xf_win_score < xf_max` is a **self-diagnosing contradiction on the
row itself**: no replay, no exclusion list, no arc. This generalises §12.3's
existing rule (`xf_ntied` was added so an arbitrary tie-break is VISIBLE) one
notch further:

> **§12.3, extended — record the WINNER'S OWN VALUE, not just the extremum and
> the tie count.** A tie count proves the selection was unambiguous *according to
> the selector*. It cannot detect a selector that disagrees with its own value
> Term, because both numbers are then computed by the thing under suspicion.
> The check that catches it is the winner's score, read back independently.

**This is a recommendation, not a change.** Editing `vision_crossframe_identity`
would mutate a landed rung's seed, and this rung pre-registered no such edit.

A second standing rule earned here:

> **Read the pinned rows before trusting the prose that summarises them.**
> §4.2's own characterisation fitted 78 of 272 rows, and the 194 it did not fit
> are what identified the defect precisely enough to exclude six mechanisms.
> A summary of evidence is not the evidence.

---

## 7. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | `fractal` is the lowest-node-id `ShapeSignature` | **CORRECT** — #726, and it is the first element the `Argmax` fold sees, which is why "the constant wrong winner" is `fractal` specifically and not an arbitrary name. It also paid a dividend I did not predict: forcing the all-tie case measured `xf_ntied = 33`, which **excludes** the tie explanation the prediction was reaching for (§4.1) |
| 2 | the scope fallback is a real latent defect that reproduces on demand, **and is NOT the cause** | **CORRECT on both halves** — reproduced (36 where 0 is correct), fixed, and excluded by the measured `unrestricted == xf_max` identity (768/768) |
| 3 | the §4.2 rows will **not** reproduce | **CORRECT** — 0 foreign wins in 1 088 000 probes. Registered in advance as a predicted NULL precisely so it could not be dressed up afterwards as a discovery |
| 4 | if one mechanism explains all three facts it will be a cache/derivation effect making the value constant inside the `Argmax` binder | **WRONG** — and wrong in the most useful direction. Both candidates are positively excluded (no cache covers `Argmax` or `ShapeDecode`; no production path attaches a derivation). I had reasoned to that class by elimination rather than from evidence, and elimination was exactly the wrong instrument: it named the only class I had not yet checked, not the class most likely to be true |

**One of four wrong, and it was the one I held with lowest confidence and stated
as a residual.** The three I was confident about were structural claims
checkable against the source; the one that failed was an inference from "what
else could it be", which is the reasoning this rung's whole method exists to
distrust.

---

## 8. SCOPE (§8)

One anomaly, one rung's seed, one engine build, one machine. The exclusions in §4
are properties of the **source** at `eb403264` and are as strong as source
reading plus targeted measurement can make them; the null in §2 is a property of
**this machine and this budget** and bounds nothing about a different one. The
fix in §3 is gated by a test and audited against the committed seeds; the defect
in §5.2 is **reported, not fixed, and not reproduced** — it is named so the next
rung to touch differential firing inherits it rather than rediscovers it.
