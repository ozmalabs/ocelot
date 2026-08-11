# The Capability Graph — the agent's measured self-model of competence

The Jabberwock models its own competence as a graph, and computes two flows over
it with its own rule engine (`seeds/capability_graph.json`, evaluated by
`run_rules` — no Python decisions). From those two flows, one measured quantity —
**leverage** — predicts mastery, transfer, expert brittleness, the difference
between *kinds* of expertise, and even why one mind reads as "magic" to another.
This document is the theory; the seed + tests are the implementation.

It is, at bottom, **algorithmic optimisation and inner-loop tuning applied to
cognition** — the same machine the runtime already runs on Terms (`l2_adaptive.rs`:
hot counter → tier-up threshold → compiled-artefact cache → deopt), lifted from
DSL Terms to cognitive capabilities.

---

## 1. The graph and its two flows

A **Capability** is a node with an `own_proficiency` (how trained the skill *itself*
is). A `composes_on` edge from A to B means *A is built through B* (B is more
foundational). Two flows are computed to fixpoint:

- **Leverage — backward, recursive centrality.**
  `leverage(B) = own_value(B) + damping · Σ_{A composes_on B} leverage(A)`.
  A capability depended on by high-leverage capabilities is itself high-leverage
  (PageRank on "composes-on"). Foundational, widely-used skills score high. This
  *is* core-ness — measured, not enumerated.

- **Effective capability — forward, multiplicative composition.**
  `eff_cap(A) = own_prof(A) · Π_{A composes_on B} eff_cap(B)`.
  Composed capability is the **product**, not the sum. A weak link drags the whole,
  and the competence-vs-mastery gap (0.9ᵏ vs 0.99ᵏ) widens *exponentially* with
  composition depth k. This is the compounding-error wall: competent-per-step fails
  over long chains; mastery of the core is the base of the exponent for everything
  built on it.

`leverage` also modulates the sufficiency throttle (`~0.9 and move on` for a
low-leverage blob → `toward 1.0, never done` for a high-leverage core) and derives
a `stage` region (blob / peripheral / core) — a label on the continuous axis, never
a set flag.

---

## 2. Mastery is multiplicative → the generalist approaches the expert

Because capability is a product, a **generalist** with mastered core (~0.98) and
only *thin* domain familiarity (0.5) overtakes a **domain expert** with mastered
domain (0.95) built on ordinary core (0.8) — once the task composes deeply enough.
The expert's ordinary core decays as 0.8ᵏ while the generalist's holds. Measured:

| depth k | generalist | expert | leader |
|--------:|-----------:|-------:|:-------|
| 1 | 0.490 | 0.760 | expert |
| 3 | 0.471 | 0.486 | expert |
| **4** | **0.461** | **0.389** | **generalist** |
| 6 | 0.443 | 0.249 | generalist |

Crossover at k≈4, then the generalist pulls away. Passing familiarity with a field,
on a maxed core, starts you near expert working level.

The meta-skill that makes it happen is **"this is like X but Y"**: a new field
enters by shape-matching to a mastered analogue X (inheriting X's mastered
decomposition) plus the shape faculty that saw the analogy. Recognising "like X but
Y" and reusing mastered structure beats rebuilding the field from thin novel parts
by ~7×. And **shape-matching, being what every analogy composes on, computes as the
highest-leverage capability** — the thing to master first.

---

## 3. Core-ness is measured *and dynamic*

A capability's leverage **moves**. A blob is low-leverage for two reasons at once —
not yet dependable enough to build on, and nothing built on it. As it is mastered
(becomes dependable) and used (dependents accrue), its centrality climbs and it
re-prices blob → peripheral → core. Bidirectional: a capability whose dependents
wither, or that a better substrate displaces, demotes. (Graph-understanding as a
"vague blob six months ago, core now" is exactly this climb.)

The seed-vs-growth-vs-mastery capital staging follows: **curiosity** funds blobs
speculatively (pre-leverage — you must run a thing to profile it), the
**leverage-economy** funds capabilities once dependents accrue, and the expensive
exact-mastery path unlocks where leverage — and therefore multiplicative ROI — is
high.

---

## 4. Expertise is a *structure*, not a scalar

Two experts with **identical** effective capability in a domain can have opposite
capability graphs. The discriminator is **genericity** — the mean leverage of the
foundations the mastery routes through:

- **High genericity**: the domain skill was consolidated onto *generic, high-leverage
  stacks* (shared across many domains). Transfers.
- **Low genericity**: a *domain-private tower* of low-leverage skills. Brittle.

`eff_cap(D)` cannot tell them apart; genericity can, and it *predicts the boundary*:

| | eff_cap(home) | genericity | eff_cap(adjacent) |
|---|---:|---:|---:|
| generic-stack expert | 0.510 | 4.60 | 0.510 — transfers |
| private-tower expert | 0.510 | 1.60 | 0.358 — collapses |

So **"expert in D" underspecifies** — you must know *how* they are expert. And the
highest meta-skill is being an **expert at *being* an expert**: consolidating every
domain onto generic stacks (via shape-matching), so the expertise transfers by
construction. That policy is itself maximally high-leverage — it applies to
mastering *any* domain.

### Expert brittleness (well observed)

The flip side, and the model predicts it exactly. A domain expert's competency
collapses the moment they drift into a surrounding area — chess masters hold no edge
on random boards; experts over-apply domain heuristics off-distribution. The expert
mastered **low-leverage, domain-private** nodes with no `composes_on` edge into the
neighbour, so off-domain the tower has nothing under it and they fall back to
ordinary core:

|  | home domain | one step out |
|---|---:|---:|
| **expert** | 0.673 | **0.164** (76 % collapse at the boundary) |
| **generalist** | 0.461 | 0.369 |

In the surrounding area the generalist's mastered core beats the collapsed expert —
and leverage names the cause (mastered nodes: expert-tower 1.60 vs gen-core 2.20).
**Leverage is the transfer predictor.**

---

## 5. It is algorithmic optimisation / inner-loop tuning

The whole model is a **profiling-guided optimiser**, and the runtime already runs
one on Terms (`l2_adaptive.rs`). Every piece maps:

| capability graph | L2 JIT (Term grain) | optimiser name |
|---|---|---|
| leverage-centrality | `HotCounter` firing counts | profile / hotness |
| mastery of high-leverage | tier-up past `threshold` → compile | optimise the inner loop |
| genericity / consolidate-to-generic | shared compiled routine, high fan-in | hoist hot code into a library |
| net-economy `worth = residual − cost` | `code_size_bytes` + tier-up cost | the cost model |
| leverage-modulated sufficiency | `TierUpPolicy.threshold` | don't compile cold paths |
| leverage is dynamic (blob↔core) | `cooling_threshold` / re-hot | hotness decays, re-profile |
| curiosity seeds blobs | interpret to gather counts | you must run it to profile it |
| sleep consolidation | AOT recompile offline | batch-optimise between runs |
| expert brittleness off-domain | epoch-stale artefact → deopt | PGO overfits its profile |
| "this is like X but Y" | cache hit → dispatch compiled artefact | route to an existing primitive |

Three things we built are **one machine at three grains** — the L2 hot-counter
(Term), the net-economy's worth (net), and capability leverage (competence) — sharing
one profiler and one cost model, read at three tiers. The cost model is now **built**
(`cap_tier_up`): `worth = value − cost`, act when worth clears a margin and the thing
is hot enough. Fed the measured leverage/cost/hotness of the profiled net-economy
rules, it masters the hot central rules and leaves the cold sink:

| capability (rule) | leverage | own_prof (efficiency) | worth | master? |
|---|---:|---:|---:|:--|
| `reflex_trial_judge` / `_refuted` | 17.4 | 0.70 / 0.91 | 17.2 | ✓ |
| ledger `credit` / `debit` | 12.8 | 0.86 / 0.89 | 12.7 | ✓ |
| `net_admit_when_worth_positive` | 3.2 | 0.96 | 3.18 | ✓ |
| `net_retire_when_worth_negative` | 2.0 | 0.98 | 1.99 | — |

That is the *same* `worth = value − cost`, act-when-it-clears-the-margin decision the
net-economy makes to **admit** a reflex net (`net_residual − net_cost − footprint >
admit_margin` over the ledger window) and the L2 JIT makes to **compile** a hot Term
(`HotCounter ≥ threshold`, worth its `code_size_bytes`). One profiler, one cost model,
three grains: compile a hot Term, admit a hot net, master a hot capability.

---

## 6. Magic — a mind reading as inexplicable to another

**"Magic" is the residual of a failed theory-of-mind**: the part of another agent's
competence you cannot reconstruct by simulating them on your own capabilities. ToM
runs by shape-matching the other's operation onto skills *you* hold; what won't
match is surprise, felt as magic.

`legibility(observer → target) = meta_capacity(observer) · (structural_base +
(1−structural_base) · content_overlap)`, `magic = 1 − legibility`, where
`content_overlap` is the fraction of the target competence's foundations whose shape
the observer also holds, and `meta_capacity` is the eff_cap of the observer's own
mind-modelling core (ToM + shape-matching). The whole thing is **gated
multiplicatively by meta_capacity** — the generic modelling core *is* the toolkit
for representing other minds.

It is asymmetric, and both directions of the observed phenomenon fall out. Measured:

| model attempt | legibility | magic |
|---|---:|---:|
| generalist models the specialist | 0.332 | 0.667 |
| specialist models the generalist | 0.070 | **0.930** |

- **Tower expert → generalist**: no shared content *and* an atrophied modelling core
  → the generalist is near-pure magic ("I can't even represent how you do that").
- **Observer → tower expert, off-domain**: they meet the low-genericity presentation,
  can't see the hidden tower, and — modelling competence as a *scalar* — can't
  reconcile "apparently useless" with "does X." Hence "how does this person manage
  to do that job?"

Legibility flows *down the genericity gradient*: whoever holds the mind-modelling
core can read many others (content where shared, structure where not); whoever
consolidated it away finds most people magic. This is why ToM and shape-matching sit
at the top of the leverage ranking — they are the nodes the graph uses to model
*other graphs*. A hard design consequence for the Jabberwock: **the set of minds it
can comprehend is bounded by its own genericity.** Master the generic modelling core
and the set of legible minds expands.

---

## 6a. The real finding — a new frame is a dimensional transform

Put the pieces together and the arc lands back on the substrate's founding loop.
Capability is multiplicative composition **over shapes**; genericity is holding those
shapes **across frames**; and the sd-loop already knows that *transformation is a
quantum change in a specific dimension* — a change of coordinates, not new structure.
So:

> **For a sufficiently meta-skilled individual, a new frame requires only dimensional
> transforms of held generic shapes, and almost no new actual skills.**

Entering a field decodes on the Occam ladder at **rung 2** (transform in the existing
basis) — occasionally **rung 3** (infer the dimension) — almost never **rung 4** (mint
novelty). Measured: an agent holding the generic base-shapes (in *other* frames) enters
a new 5-shape frame at **0 new skills / 5 transforms**; a narrow agent holding only two
must mint **3 of 5** anew (new-skill fraction 0.60). As genericity rises, the new-skill
fraction → 0.

This is also what a generalist's "magic" fluency in a new field *is*, mechanically:
they are **transforming skills they already hold**, not acquiring new ones — which is
exactly why it's cheap, why it transfers, and why it's invisible to an observer who
would have to mint the whole tower. The capability graph and the dynamic-quantization
transform ladder are one machine: a new domain is a coordinate transform on held shape.

## 7. Implementation — the Jabberwock's own self-model

All of the above is graph data the agent computes with its own rule engine, no
Python decisions:

- `seeds/capability_graph.json` — a `CapabilityPolicy` singleton of tweakable knobs
  and six fixpoint rules: `cap_leverage_propagate`, `cap_effective_compose`,
  `cap_sufficiency_from_leverage`, `cap_stage_from_leverage`, `cap_genericity`,
  `cap_model_legibility`. All expressible in the existing DSL (`InNeighbours`, `Sum`,
  `Prod`, `Pow`, `MaxOver`, `Exists`, `Filter`) — no Rust added.
- `domains/capability_graph.py` — mechanical host I/O only (mint / compose /
  `like_but` / agents+ownership / model attempts / settle / readers). No conditional
  chooses anything; the rules do.
- `tests/test_capability_graph_migrated.py` — 9 gates covering every claim above.

## The capstone — measured, not authored (built)

The graph no longer has to be hand-wired. `domains/capability_profiler.py` measures it
from the agent's own activity:

1. A real workload runs on `run_rules`. **Which** rules fired, and how hard, is read
   straight from the engine's own counters (`substrate.rule_costs()` →
   `(name, µs, processed, progressed)`) — the same hot-path signal the L2 JIT tiers on.
2. The `composes_on` dataflow is **derived from the rules themselves** — rule B
   composes_on rule A iff B *reads* an attr A *writes* (the producer/consumer accounting
   the Rust engine already does in `derive_access`). Nothing is authored.
3. The existing `cap_leverage_propagate` rule computes leverage over that measured graph.

Run on the net-economy chain, with no `composes_on` edge written by hand, the profiler
recovers the structure and ranks it (measured leverage):

| capability (rule) | leverage | role in the dataflow |
|---|---:|---|
| `reflex_trial_judge` / `_refuted` | 17.4 | source — everything reads its `verdict` |
| `net_ledger_credit_hit` / `_debit_miss` | 12.8 | ledger — reads verdict, feeds the totals |
| `net_admit_when_worth_positive` | 3.2 | sink — reads the totals |
| `net_retire_when_worth_negative` | 2.0 | sink |

The judge — the reflex-net design's "one genuinely new decision" — surfaces as the
highest-leverage capability from the agent's own activity, unwired. That is the agent
measuring its own competence structure: a profiler over `run_rules`, leverage as
hotness-plus-centrality, read at the capability grain.

Everything above is now **built** end to end. The profiler measures each rule's `cost`
(µs), `own_proficiency` (efficiency — cheaper per firing reads as more mastered), and
the unified cost model (`cap_tier_up`, §5) makes the master decision with the same
`worth = value − cost` shape as the net-economy admit and the JIT tier-up. And the two
honest limits are closed:

- **Correctness proficiency.** `cap_correctness_from_trials` generalises the reflex-net
  judge to any capability: a `CapabilityTrial` carries a `supported`/`refuted` verdict
  from an oracle, and `correctness = supported-rate` becomes the capability's
  `own_proficiency`, so effective capability reflects *right* answers, not just cheap
  ones (8/10 → 0.8). Honest floor: correctness is defined against an *oracle* — there is
  no oracle-free correctness; the agent measures the hit-rate its oracle (cognition, the
  slow path, the environment) reports, exactly as a reflex net is judged against the
  cognition it caches.
- **Sharpened dataflow.** A `composes_on` edge now means genuine *consumption* — B reads
  a key A writes that B does **not** itself write — which excludes shared-accumulator
  keys, makes the measured graph a **DAG**, and lets multiplicative `eff_cap` compose
  cleanly (no cyclic collapse) instead of falling to 0 on a `credit ↔ debit` cycle.

And the last two sharper edges are now closed too:

- **Type-qualified dataflow.** Read/write sets are keyed by `(node_type, key)`, resolved
  from each rule's match edges via the seed's productions — so `status` written on a
  `ReflexTrial` and read on a `ReflexNet` no longer collide. The false `admit → judge`
  edge disappears while the real `credit → judge` (`verdict`) edge survives; types
  resolve the overlaps, and the control-key exclusion is no longer needed.
- **A standing oracle in `run_rules`.** The reflex-net judge already verdicts trials
  supported/refuted as the graph ticks; `cap_harvest_reflex_verdict` turns each into a
  `CapabilityTrial` on the net, so `correctness → own_proficiency` accrues **live** in
  one fixpoint (8/10 supported → 0.8) with no hand-supplied trials. Wherever a
  capability's firing is judged against ground truth in the loop, correctness flows into
  the self-model continuously.

The self-model is now measured end to end from the agent's own activity — structure,
leverage, cost, worth, efficiency, and oracle-judged correctness — all computed by the
agent's own rules over `run_rules`.
