# ENGINE CORRECTNESS — THE `Argmax` NON-REPRODUCIBILITY — PRE-REGISTRATION

*Branch `gamma-substrate/engine-argmax-determinism`. Seed block **56000–56999**
(allocated before launch; a concurrent rung holds 57000–57999 — this rung takes
NO seed outside its block).*

*Committed BEFORE any measurement is run, per §3. The engine is built in THIS
worktree (`scripts/engine_build.sh`), never in the canonical tree (§11).*

---

## 0. WHAT THIS RUNG IS

This is **not** a vision rung and it registers **no hypothesis about vision**. It
is an engine-correctness investigation of the defect recorded at
`VISION_CROSSFRAME_IDENTITY_RESULTS.md` §4.2 (merged `50448c82`), whose evidence
is pinned at `results/crossframe_identity_anomaly_rows.json` — **the one artifact
in this investigation that is not regenerable. It is read-only evidence and is
not overwritten by anything here.**

**The primary deliverable is a DIAGNOSIS WITH A REPRODUCTION, or an honest
statement that it could not be reproduced plus the narrowest provable bound on
what is affected.** A fix without a reproduction is untestable, so **no fix will
be committed unless a reproduction exists that is RED before it and GREEN after
it**, both demonstrated. A plausible cause presented without a reproduction is a
guess and will be reported as one, or not at all.

---

## 1. THE OBSERVATION, RESTATED FROM THE PINNED EVIDENCE ONLY

C1, base frame 18, k=4: **all 272 of that base frame's probes returned the held
signature `fractal`** — a `ShapeSignature` installed by `boot_core` /
`shape_decode_loop`, not one of the 16 tiles. `fractal`'s `signature` uses
predicates (`build`/`refers`/…) that `ShapeDecode`'s `covers_relation` can never
match against a `["cell", r, c, "v<q>"]` goal, so its `covered_count` against any
probe in this rung is necessarily **0**. It is not a defensible tie-break; the
returned winner provably cannot cover a single goal relation.

**§4.2's characterisation of the rows is incomplete, and the correction sharpens
the target.** §4.2 describes the rows as "each records `xf_max = 36`,
`xf_ntied = 1`, `true_score = 36`". Read directly off the pinned file, that
describes **78 of the 272 rows**, not all of them. The complete picture is:

| fact | value over all 272 rows |
|---|---|
| `said` | `fractal`, 272/272 |
| `xf_max` | spread over 9…36 (24 distinct values) |
| `xf_ntied` | spread over 1…5 |
| **`xf_max == nn_score`** | **272 / 272** |
| **`xf_ntied == nn_ties`** | **272 / 272** |

`nn_score` / `nn_ties` are computed **outside the graph, in numpy**
(`crossframe_world.hamming_nn`). So on every one of the 272 anomalous rows:

- **stage 1 (`xf_score`'s `MaxOver`) is CORRECT** — it agrees with the numpy
  Hamming maximum, every row;
- **stage 2's `Count(Filter(Eq(ShapeDecode, xf_max)))` is CORRECT** — it agrees
  with the numpy tie count, every row;
- **stage 2's `Argmax` is WRONG, and wrong the SAME way every time** — the same
  single node, for every probe in that substrate, whatever the probe was
  (including the G1 identity probes and the G2 pure-noise probes).

**This is a sharper defect than §4.2 states, and a different shape.** It is not
"an `Argmax`/`Eq` disagreement scattered across a rule". It is: **one `Argmax`
returned one constant node for an entire substrate's worth of evaluations, while
two structurally identical `ShapeDecode` compositions in the same seed — one in
the preceding rule, one in the very next effect of the same rule application —
were simultaneously correct.**

**Everything below is registered against THAT restatement**, which is derived
from the pinned rows alone and is checkable by anyone from that file.

---

## 2. HYPOTHESES, TWO-SIDED, EACH WITH A DISCRIMINATING TEST

Every hypothesis must explain **both** halves at once: the constant wrong
`Argmax`, **and** the simultaneously correct `MaxOver` and `Count(Filter(...))`.
A hypothesis that explains only one half is recorded as **insufficient**, not as
a partial answer.

**H1 — DEGENERATE ARGMAX ON AN ALL-EQUAL COMPARISON.**
`argmin_or_argmax_over` (term.rs) takes the new element only on a strict
`Ordering::Greater`, so **the first element of the source wins every tie**.
`NodesOfType` returns `Value::make_frozenset(...)`, which canonicalises by
`cmp_value` — for `Value::Node` that is **ascending node id**. The `boot_core` /
`shape_decode_loop` signatures are created before the 16 tiles, so a foreign
signature is **first**. If, inside the `Argmax` only, the `value` Term evaluated
to the same value for every candidate, the `Argmax` returns the lowest-id
`ShapeSignature` unconditionally.
*Prediction:* `fractal` is the lowest-id `ShapeSignature` in a booted
`CrossFrameWorld`. *Two-sided:* if it is not lowest-id, H1 is dead as stated.

**H2 — SCOPE FALLBACK: an empty `codebook_scope` silently means UNRESTRICTED.**
`apply_scope` (shape_decode.rs) builds its scope set with a `push` closure that
matches **`Value::Str` only** and drops every other shape, then applies the
scope **only `if !scope.is_empty()`**. So a `codebook_scope` whose element is
not a `Value::Str` — notably a `Value::Surface(Text, ..)`, which is the ONLY
shape a rule-built string can have, and which this same file's own
`str_shaped` / `string_attr_or_panic` exist to accept — yields an empty set and
therefore **the whole codebook**, scoring that candidate the GLOBAL maximum
instead of its own. `apply_exclude` has the identical shape.
*Prediction:* a `ShapeSignature` whose `name` is a `Surface(Text)` scores the
global max under this seed's per-candidate scoping. *Two-sided:* if a
`Surface`-named entry scopes correctly, H2 is dead.
*Sufficiency note, registered in advance:* H2 alone predicts the affected
candidate ALSO passes the `Eq(·, xf_max)` filter, which would make
`xf_ntied` = `nn_ties` + 1. The rows show `xf_ntied == nn_ties` exactly. **So H2
is registered as INSUFFICIENT on its own** and can only be part of the answer in
combination with something that makes the two sites differ.

**H3 — A CACHE MAKES THE `value` TERM CONSTANT INSIDE THE BINDER.**
`EvalCache.filter` is keyed `(TermIdx, free-var bindings)`. If the free-var
capture for a cached subterm omits the enclosing binder's variable (`sig`), a
cached value computed under one binding is served under all the others — making
the `Argmax`'s per-candidate value constant while a differently-shaped site
recomputes. *Test:* whether the crossframe path opens an `EvalCache` at all;
whether `free_vars` captures the binder variable through every node type on the
path from `Argmax` to `ShapeDecode`.

**H4 — A GRAPH-RESIDENT DERIVATION REPLACES NATIVE `Argmax`.**
`DerivationRegistry` is explicitly dynamic ("the agent installs / replaces /
removes entries between evaluations") and `Argmax` is named as a `BodyTaker`
derivable variant. A derivation installed at some point in a long process would
route `Argmax` through an expansion whose tie/order semantics need not match
`argmin_or_argmax_over` — and would not be present in a fresh short replay.
*Test:* whether any registry entry for `Argmax` can be installed on this path,
and whether the expansion's semantics differ from the native fold.

**H5 — PER-PROCESS HASH ITERATION ORDER.** Rust's default hasher is randomly
seeded per process; `std::collections::HashSet` is used in `apply_scope`,
`apply_exclude`, `BeamState.used` and the beam `seen` dedup. *Largely
pre-excluded* for the `Argmax` SOURCE (`make_frozenset` sorts), so the test is
whether any of these sets is **iterated** rather than only queried for
membership.

**H6 — INTEGER WRAP IN `covered_count`.** `Value::Int((n_goal - residual.len())
as i64)` is a `usize` subtraction. If `residual.len() > n_goal` it wraps.
*Prediction:* wrapped values are negative (`-k`), so they cannot win an `Argmax`
over non-negative scores. Registered so it is excluded on the record rather than
by assumption.

**H7 — THE NULL: it is none of these, and it does not reproduce.** Registered
explicitly as a permitted outcome (§7 of the protocol). If so the deliverable is
the ruled-out list with the evidence for each exclusion, plus the bound of §4.

---

## 3. THE STATISTIC, AND THE DECISION RULE

There is no proportion to estimate here and **no CI is claimed**. The unit is a
**reproduction**, and the decision rule is binary and stated in advance:

- **REPRODUCED** iff a test exists that, on the pinned engine source, makes an
  `Argmax` return a node whose `value`-Term score is strictly less than another
  candidate's, **and** that same test is GREEN after the fix. The test must be
  committed and must be RED before the fix in the same working tree, with both
  outcomes shown.
- **NOT REPRODUCED** otherwise. In that case **no Rust is changed**, and the
  report is the exclusion list plus §4's bound. A latent defect found by reading
  (e.g. H2) that is NOT demonstrated to produce the observed rows is reported as
  **a separate latent defect with its own reproduction**, and is explicitly NOT
  claimed as the cause of §4.2.

**Stress budget, fixed in advance** (no sweeps, no re-runs to taste):
`N_PROC = 200` independent processes for any process-varying probe, and
`N_HISTORY = 20` sequential worlds within a process to cover base-frame-18's
position in the original run. These numbers are chosen because the original
anomaly was 1 world in 100 with 0/5440 on replay; 200 × 20 is the largest budget
that fits the time box, and is registered so a null is a null and not "run it
again".

---

## 4. THE BOUND — WHAT MUST BE REPORTED WHATEVER THE OUTCOME

Because this failure is **silent** (a confident wrong answer with
internally-consistent metadata), the report must state, for whatever cause is or
is not established:

1. **Which Term compositions are exposed** — precisely, by structural criterion,
   not by example.
2. **Whether any LANDED result in this tree uses such a composition**, found by
   an audit of the committed seeds, not by recollection.
3. **The narrowest bound provable on the blast radius**, including "unbounded,
   because the cause is not established" if that is the honest answer.

This rung **does not re-run any other rung's results.**

---

## 5. MY PREDICTIONS, IN ADVANCE (§3.7)

1. `fractal` **is** the lowest-node-id `ShapeSignature` in a booted
   `CrossFrameWorld`. *(Confidence: high. If wrong, H1 dies and the "constant
   wrong winner" needs a different mechanism entirely.)*
2. H2's `Surface`-name scope fallback **is** a real latent defect that
   reproduces on demand. *(Confidence: high — it is visible in the source.
   Proviso, registered: it is insufficient for §4.2 by the `xf_ntied` argument
   above, and I predict it is NOT the cause.)*
3. The §4.2 rows themselves **will NOT reproduce.** *(Confidence: moderate.
   5 440 probes already failed to reproduce them; I expect my budget to fail
   too, and I expect the honest deliverable to be an exclusion list plus at
   least one separately-reproducible latent defect.)*
4. If a single mechanism does explain all three facts at once, I predict it will
   be **an evaluation-order or cached-state effect that makes the `value` Term
   constant inside the `Argmax` binder only** (H3/H4 class), because that is the
   only class that leaves `MaxOver` and the `Filter` correct. *(Confidence:
   low — this is the residual after the others, not a positive finding.)*

I expect prediction 3 to be the one that decides the shape of the report, and I
am registering it as a predicted NULL so that a null cannot later be dressed up
as a discovery.

---

## 6. WHAT WOULD MAKE ME WRONG

- Any `Argmax` in the tree that can return a strictly-suboptimal element under
  a deterministic, reproducible input kills prediction 3 immediately.
- If the `xf_ntied == nn_ties` identity in §1 is itself an artifact — e.g. if
  `nn_ties` and `xf_ntied` can agree for reasons unrelated to correctness —
  then §1's restatement is wrong and every hypothesis above is aimed at the
  wrong target. This is checked FIRST, before anything else is run.
