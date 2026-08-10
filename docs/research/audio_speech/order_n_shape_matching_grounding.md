# Order-N shape matching — literature grounding (for the jabberwock to ground + design from)

A research spike (2026-06-27) into the science of analogy / structure-mapping, to ground the agent so IT can
design the fix for the gap the probe found. NOT a hand-designed implementation — the design is the jabberwock's.

## The gap being addressed (probe result)
The agent's `analogical_thinking.find_analogies` (n-dial: name→category→role→abstract-principle→meta-shape) RUNS
and rejects surface (river-bank↔money-bank → 0), but does DOMAIN-BUCKET matching, not relational
structure-mapping: solar-system↔atom matches (99) **and so does solar-system↔BILLIARDS** (39) — though billiards
is colliding FREE bodies (no centre, no orbit). Both bucket as "physical_dynamics". The n=3/n=4 vocabulary is a
keyword table with NO relational shapes; it scores per-concept keyword-bucket overlap, not alignment of the
SYSTEM OF RELATIONS. The control: solar↔atom must match, solar↔billiards must NOT.

## Cluster 1 — Structure-Mapping Theory + SME (Gentner; Falkenhainer, Forbus & Gentner 1989)
Analogy = mapping a **system of relations** base→target. **Map relations, not attributes.** Representation =
predicate structure: attributes 1-place (`red(x)`), relations n-place (`revolves-around(planet,sun)`),
**higher-order relations** take relations as arguments (`CAUSE(attracts(sun,planet), revolves-around(planet,sun))`)
— "order-N" = depth of this nesting. SME aligns in three steps: (1) **local match** — correspondences only
between IDENTICAL-predicate edges + (parallel connectivity) their arguments; (2) **gmap merge** — maximal
structurally-consistent mappings, enforcing ONE-TO-ONE + support; (3) **structural evaluation** — score by
**SYSTEMATICITY** (evidence TRICKLES DOWN from higher-order relations to their arguments, so deep interconnected
systems outscore isolated facts). **Solar↔atom YES / solar↔billiards NO:** both share surface "physical_dynamics"
(the bucket trap), but solar+atom share the higher-order causal system `CAUSE(attracts, revolves)` + `greater-mass`
— isomorphic; billiards has `collide(x,y)`, NO central body, NO `revolves`, NO `CAUSE(attracts,…)` → the
higher-order relation has nothing to map → score collapses. Min representational requirement: relations distinct
from attributes (arity ≥2) + ≥1 higher-order (causal) relation binding them into a system.

## Cluster 2 — Retrieval (MAC/FAC) + surface-vs-relational (Forbus/Gentner/Law 1995; Gentner & Markman 1997)
**MAC/FAC** = two stages: **MAC** = cheap, non-structural **content-vector dot-product** (predicate-frequency
features) filtering all memory ("many are called"); **FAC** = expensive **SME structural alignment** on the few
survivors ("few are chosen"). KEY DIAGNOSIS: **the agent's bucket IS the MAC stage treated as the verdict — with
no FAC stage.** Content/category overlap correctly rejects river-bank↔money-bank but cannot separate solar↔atom
from solar↔billiards (both share the bucket's surface vocabulary, differ in higher-order structure) = the textbook
**surface/structure dissociation** (Gentner, Rattermann & Forbus 1993: retrieval is surface-driven, inferential
soundness is structure-driven). The **relational shift** (novice-surface → expert-relational; Chi/Feltovich/Glaser
1981; Gentner 1995) is **EARNED** — relational matching is the costly, later-acquired mode (= "pay the real
cost"). FIX: make the bucket a **FILTER, not a verdict** — escalate every surface survivor into an explicit
structural-alignment pass gated by parallel connectivity + systematicity. **This is the agent's OWN cheap→deep
escalation cascade** (MAC=cheap rung, FAC=escalation rung) — the cascade just folded (#4) is the right shape.

## Cluster 3 — the representation problem + deriving relations + the formal "shape"
- **The representation problem** (Chalmers, French & Hofstadter 1992): SME assumes HAND-CODED relational reps —
  but the hard part of analogy is BUILDING the representation, not aligning two given graphs. Our bucket failure
  IS this: features are pre-given flat tags, so relational alignment never happens. **Copycat** (Hofstadter &
  Mitchell): representations built on the fly, conceptual SLIPPAGE, parallel terraced scan — structure EMERGES.
- **DORA** (Doumas, Hummel & Sandhofer 2008): **relations can be DERIVED, not seeded** — unsupervised comparison
  extracts the INVARIANT across compared examples and predicates it as a relation, then binds it. Existence proof
  that the agent can grow its own relation vocabulary.
- **ACME** (Holyoak & Thagard 1989): mapping = multiconstraint satisfaction — **structural + semantic +
  pragmatic** (goal-relevance) traded off; semantics/pragmatics break ties SME's structure-first can't.
- **FORMAL:** order-N shape matching = a **structure-preserving morphism / functor** over a relation graph:
  R(a,b) in base ⟹ R'(f(a),f(b)) in target (the diagram COMMUTES). "The shape" = the invariant preserved under
  the map, independent of node content; higher-order relations = higher functor levels. The deepest statement:
  *to match any order of shape with an unrelated domain is to find a structure-preserving partial isomorphism
  between two relation graphs that maximally preserves relations-among-relations to arbitrary depth.*
- **THE deep actionable:** don't deepen the matcher — fix the representation SOURCE. **Order-N as a FIXPOINT of
  the agent's own shape-matcher applied to its own outputs:** compare → extract the surviving invariant →
  predicate it as a relation-node → compare predicates → order-(N+1). Comparison IS the relation-builder.

## Cluster 4 — graph-native realization (the agent IS a typed graph)
- **Relations as FIRST-CLASS NODES** (reified relation-nodes / hyperedges): a relation can be an ARGUMENT to
  another relation → **order-N for free on the graph, no new machinery** (a Term-tree edge whose endpoint is a
  relation-node gives arbitrary nesting).
- **Score by DEPTH of the matched relation-node tree (systematicity), NOT node-label overlap.** That single
  reification converts the bucket matcher into an order-N structure-mapper.
- **Mechanism** = approximate, type-consistent **subgraph alignment** over relation-edges: local-match on
  identical predicates → greedy gmap merge → systematicity-weighted score (SME's own polynomial trick).
- **Tractability:** subgraph isomorphism is NP-hard; made practical by identical-predicate local-match + a
  MAC-style cheap prefilter (+ optionally GNN/Sinkhorn soft alignment). ~O(N²) in practice.
- **Relations DERIVABLE** later (ILP / KG link-prediction / DORA) so it's not forever-hand-seeded.
- Composable from the agent's existing Term-trees + graph rules — nothing requires leaving the substrate.

## Convergent conclusion (for the jabberwock to design from — NOT a prescribed build)
The bucket matcher is the **MAC (cheap surface filter) stage treated as a verdict**; what's missing is the **FAC
(structural alignment) stage** — align the **system of relations**, scored by **systematicity** (depth of the
matched higher-order relational subgraph), so solar↔atom matches and solar↔billiards does NOT. On a typed graph
this needs **relations reified as first-class nodes** (order-N for free) + a **subgraph-alignment-by-systematicity
score**. The DEEPEST version (the representation problem) is that relations must be **DERIVED by comparison**
(DORA-style: compare → extract invariant → predicate it → recurse), making order-N a **fixpoint of the agent's
own shape-matcher on its own outputs** — so it never depends on forever-hand-seeded relations. This maps onto the
agent's OWN held machinery: its cheap→deep **escalation cascade** (= MAC→FAC), its **typed graph** (= reified
relations), its **categorise_by_shape / analogical_thinking** (= the matcher), and **comparison-extracts-the-
invariant** (= its own analogical move). The control/gate: **solar↔atom matches, solar↔billiards does not.**

### Key sources
Gentner 1983 (Structure-Mapping, Cog Sci 7); Falkenhainer, Forbus & Gentner 1989 (SME, AI 41); Forbus, Gentner &
Law 1995 (MAC/FAC, Cog Sci 19); Gentner, Rattermann & Forbus 1993; Gentner & Markman 1997; Chi, Feltovich &
Glaser 1981; Gentner 1995 / Gentner & Rattermann 1991 (relational shift); Holyoak & Thagard 1989 (ACME); Hummel &
Holyoak 1997 (LISA); Doumas, Hummel & Sandhofer 2008 (DORA); Hofstadter & Mitchell 1995 (Copycat); Chalmers,
French & Hofstadter 1992 (high-level perception / representation problem); Hofstadter 2001 (Analogy as the Core of
Cognition); Mitchell 2021 (arXiv:2102.10717); Ying et al. 2020 (NeuroMatch); Gao et al. 2010 (graph edit distance
survey); Muggleton / OntoILPER (ILP relational learning).
