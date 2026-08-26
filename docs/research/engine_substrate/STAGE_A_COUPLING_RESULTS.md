# The settling measurement — the coupling test is incomplete, and the cost model changed underneath it

Prediction registered at `472b303`, before this measurement existed:

> *"does batching the uncoupled 56.3% differ from running them to fixpoint, on any workload? On the
> theory it should be **byte-identical**, and if it is not, the coupling test is incomplete in the
> same way the write-set relation was."*

**It is not byte-identical. The coupling test is incomplete, in a precisely nameable way — and the
divergence that earlier work recorded as "benign" is not benign under the revised theory's own cost
model.**

## Measured

Stage A ON + compare mode, which derives every drain BOTH ways and diffs the write lists.

| workload | excluded (coupled → fixpoint) | compared (uncoupled → both) | diverged | **UNSOUND** |
|---|---|---|---|---|
| `learning_progress` | 569,001 | 37,356 | **0** | 0 |
| `psychosis_grounding` | 0 | 13,350 | **0** | 0 |
| 24 migrated suites | 4,072,966 | 228,360 | **58** | **0** |

Diverging rules across all of it: **exactly one**, `comprehend_familiar`. Unsound drains: **zero** —
every divergence was flagged by the existing write-set `conflicts` relation and fell back, so Stage A
never committed a wrong result.

## The one rule, and why the coupling test cannot see it

`seeds/semantic_comprehension.json`:

```
match:   [m, denotes, meaning]
where:   Count(InNeighbours(meaning, "denotes")) >= 2
effects: set_attr meaning familiar 1.0
```

Its `read_set ∩ write_set` is **empty** — it reads *structure* (in-degree of `denotes`) and writes an
*attribute* (`familiar`). By the coupling test it is uncoupled, and Stage A batches it.

But **many bindings share the same `meaning` node**: every `m` denoting one meaning is a separate
binding, and all of them write `familiar` on that one node. Verbatim from the samples:

| | |
|---|---|
| Stage A | `[SetAttr(2978, familiar, 1.0)], [SetAttr(2978, familiar, 1.0)], …` |
| committed | `[SetAttr(2978, familiar, 1.0)]` |

and where bindings hit *different* nodes, the two agree exactly.

**So the coupling is between BINDINGS SHARING A TARGET, not between a rule's reads and its writes.**
`read_set ∩ write_set` is a per-RULE predicate and structurally cannot express "these two bindings
touch the same node".

### Which corrects §5f's framing as well as mine

`STAGE_A_RESULTS.md` §5f concluded *"no refinement of a write-set relation can see one"* — of a
read-dependence. True, and this is its exact mirror: **no refinement of a read-write test can see
write contention.** The two relations are **complementary, not competing**:

| relation | detects | GALS reading |
|---|---|---|
| `read_set ∩ write_set` | one binding's write feeds another's read | **temporal** coupling |
| `conflicts` (write-set overlap) | bindings writing the same place | **contention** coupling |

Neither alone is the coupling detector my reassessment claimed the engine already had. **Together
they are**, and the engine already computes both — which is why `unsound = 0` across 279,066
compared drains.

## The part that is genuinely new: "benign" no longer means what it meant

§5g recorded the residual divergence as benign because the **graph state is identical** — N identical
writes and one write leave the same value. Under the revised theory that reasoning no longer closes:

> *"the single cost is the write, paid by the rules"* — and the falsifier: *"**Cost is the write.**
> Fails if a substrate operation other than writing a delta carries an irreducible cost."*

> **CORRECTED, immediately after publication and before anything was built on it.** The paragraph
> below originally claimed the N-versus-1 write list is *"a five-fold cost"* at runtime. **It is not,
> and I should have read the fallback path before writing it.** `substrate.rs` is explicit: *"If two
> of them write the same place they were each computed blind to the other, so the set is NOT
> independent and the sequential committed path below runs instead."* Contention **falls back**, so
> the writes that actually land are the committed ones — one, not N. The divergence is in the
> *derived proposal list*, which is then discarded. `unsound = 0` is the same fact seen from the
> other side: all 58 were flagged, hence all fell back.

The cost point survives, but it is a different cost with a different mechanism. Derivation is
apply-then-undo: on a contended drain Stage A pays **N speculative applies plus N undos, and then
the committed sequential run happens anyway**. Under *"the single cost is the write, paid by the
rules"* that is strictly **more** writing than not speculating at all — the waste is the speculation,
not the commit.

So the revised reading is narrower and still real: state-identity was never the right benignity test
under a write-based cost model, but what it hides here is **wasted speculative work on contended
drains**, not inflated committed state. That is also what a static contention test would buy —
refusing up front instead of deriving and discarding.

## What this settles

1. **The salvage in `STAGE_A_REASSESSED_AGAINST_V23.md` was half right.** `derive_access` is a
   coupling detector for the *temporal* half only. The reassessment's claim that the engine "already
   computes the discriminator" overstated it by exactly one relation.
2. **Stage A's soundness holds** where it was claimed: zero unsound drains across 279k compared,
   including the one diverging rule.
3. **Default-OFF remains right**, now for a third independent reason: not the bench falsification,
   not only the synchrony-without-coupling argument, but that batching multiplies writes on
   contended targets and writes are the cost.

## Honest bounds

24 of 683 migrated suites, chosen by fixed stride, not a full sweep — a rule that diverges only in an
unsampled suite would not appear here. Four of those suites had failing tests under Stage A ON, which
this run did **not** triage against an OFF baseline; the divergence and soundness counters are
independent of test outcome, but "24 suites pass" is not claimed and should not be read in. The
write-multiplication cost is argued from the theory's cost axiom and the verbatim samples; it has not
been measured as runtime, and under this engine it would not show up as runtime — which is precisely
why it needs the theory to be visible as a cost at all.
