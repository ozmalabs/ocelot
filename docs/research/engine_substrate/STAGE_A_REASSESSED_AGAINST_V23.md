# Stage A, re-assessed against the revised theory

The papers moved on 2026-08-26 (`87a0ba7` *the ablation to "rules run" — collapse as a local write*;
`5a684b2` *GALS… and the rule runner*; `f37fc6c` *c as the change-to-time rate, no dependent
clocks*). Stage A was designed against the earlier reading. This is the re-assessment.

**Conclusion in one line: Stage A's mechanism survives, its JUSTIFICATION inverts, and its own
refusal predicate turns out to be the thing the new theory most needs — a coupling detector.**

## What the theory now says, in the three lines that bear on Stage A

> *"Only that rules run is compulsory. Applying a delta is itself a rule, not a primitive operation
> beneath the rules."* (§Nothing compulsory)

> *"A collapse is a local asynchronous write and the only event; ordering is required but only as a
> partial order the rules carry themselves, with no substrate time and no global instant."*
> (Conclusion)

> *"The non-atomicity this implies — a graph's state may be altered by another write while its own
> rules are mid-run — **is not a defect here but the expected regime**; robustness is obtained by
> **re-running to fixed point** (a raced deformation becomes residual and is re-offered), **not by
> locking**."* (§Time is not a dimension, on Lamport/Brewer)

And the falsifier the theory volunteers against itself:

> *"**Globally-async/locally-sync.** Fails if coupling never induces local synchrony … or **if
> synchrony is forced without coupling (a global instant exists independent of any boundary)**."*

## Stage A as built

`STAGE_A_RESULTS.md`: *"Stage A derives every binding of a drain against one immutable base and
applies the resulting proposals at a single boundary."* Status: behind a flag, **default OFF**,
falsified by the full bench (§5f), falsifier then closed in §5g by **refusing** every rule whose
`read_set ∩ write_set` is non-empty — **43.7% of the corpus** (1643 of 3764).

## Three findings

### 1. The justification inverts

Stage A's premise is that same-round visibility and `apply-then-maybe-undo` are **defects to
remove** — that is how `GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` scores them (*"Non-mutating
proposal construction | LACKS"*). The revised theory says mid-run mutation **is the expected
regime**, and names the correct remedy as **re-running to fixed point, explicitly not locking**.

`run_rules` is already a fixpoint. So on the new reading **the engine's existing behaviour is the
theory-sanctioned one, and Stage A is the deviation** — not the repair. That is a reversal of sign,
not a detail.

### 2. A drain-wide immutable base is synchrony without a coupling

One base plus one publication boundary orders every binding of a drain together. That is a **local
synchronous domain**, which the theory permits — but as *"the coupled case,"* one that *"costs a
coupling write,"* against a default of asynchrony.

Stage A applies it to a drain **whether or not those bindings are coupled**. Applied engine-wide it
is a global instant independent of any boundary, which is the exact wording of the theory's own
`Globally-async/locally-sync` falsifier. **Default-OFF is therefore the right setting for a reason
better than the one recorded** (the bench falsification): even a Stage A with a perfect merge
relation would be imposing synchrony the substrate does not have.

Relatedly, `Applying a delta is itself a rule, not a primitive operation beneath the rules` bites the
commit step directly: Stage A's single-boundary apply is executor machinery **beneath** the rules,
where the theory now wants rule content.

### 3. The refusal predicate is a coupling detector — and this is the salvage

§5g refuses rules whose `read_set ∩ write_set` is non-empty, and reports the share as an
embarrassment (*"much broader than first reported"*). Under the revised theory that predicate is
exactly the question GALS turns on:

* **`read_set ∩ write_set = ∅`** — this rule's bindings do not observe each other. There is **no
  boundary coupling their collapses**, so they are asynchronous by default and may be batched
  freely. 56.3% of the corpus.
* **`read_set ∩ write_set ≠ ∅`** — one binding's write is another's read. That **is** a boundary
  relating the collapses, hence a legitimate local synchronous domain. 43.7%.

So the number is not a measure of how much Stage A must give up. **It is a measurement of how much
of this corpus is coupled** — and the engine has been computing it for free, on every rule it
installs, via `derive_access`. Nothing in the theory asks for it to be refused; it asks for it to be
*ordered*, which is what a fixpoint re-offer already does.

## What survives, and what should be re-stated

| | verdict |
|---|---|
| `derive_access` read/write sets | **survives, promoted** — reread as the coupling test GALS needs |
| "a proposal carries a **condition**, not the answer" (§5, §5c) | **survives, strengthened** — under async the state may have moved, so re-checking at commit is mandatory, not an optimisation |
| the falsifier discipline (three defects that passed every suite) | **survives** — unaffected by any theory change |
| drain-wide immutable base as the engine's round | **re-stated** — legitimate only as an *opt-in local synchronous domain declared by a coupling*, never as the default |
| single-boundary apply as executor primitive | **wrong shape** — the theory wants the merge as rule content |
| "non-mutating proposal construction is a gap the substrate LACKS" | **withdrawn** — it is a capability, not a deficiency, and its absence is not a defect |

## What is NOT concluded

No code changed in this rung, and none should on this evidence alone. In particular this does **not**
conclude that Stage A should be deleted: an opt-in synchronous domain over an uncoupled drain is
both theory-legal and useful, and `stage_a.rs` already computes the discriminator that would gate it.
What it concludes is that the flag's default is right, the framing in
`GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md`'s scorecard row is now wrong, and the 43.7% figure
should be reported as a corpus property rather than as Stage A's shortfall.

The measurement that would settle the salvage — does batching the uncoupled 56.3% differ from
running them to fixpoint, on any workload? — has not been run. On the theory it should be
byte-identical, and if it is not, the coupling test is incomplete in the same way the write-set
relation was.
