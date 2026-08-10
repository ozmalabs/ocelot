# function_shape — narrowing the search area via published prior work

> Per user: "look at the current metacognitive science and work in this area
> as a base — this is all my shape guessing, lets narrow the search area."

The pivot has three structural needs:
  · **Cache** higher-order shapes in the graph so order-N is cheap.
  · **Generic** order-N — the operator applies to any function, not just
    signal samples.
  · **Classify** every function by {recursion, order-N, abstraction
    (= order-N applied to the function itself)}.

Each need maps to an established research lineage with concrete
architectural commitments. The function_shape vocabulary should inherit
its semantics from those lineages — each concept cites a specific source.
This narrows the design space from "anything I might invent" to "what does
the cited theory actually say."

---

## Five lineages, narrowed

### 1. Smith, B. (1982/84) — Reflection and Semantics in a Procedural Programming Language (3-LISP)

**Architectural commitment:** Reflection is CAUSAL ACCESS to one's own
implementation. A function can REIFY itself into the meta level, and the
meta-level representation is first-class — itself a function that the
language can evaluate. The reflective tower means each level can examine
and modify the level below; new levels are created on demand.

**What it constrains in the pivot:**
  · `meta_shape` (order-N applied to a function rather than a signal) is
    NOT just "apply the operator to the function's text." It is
    REIFICATION — the function appears at the meta level as a graph object
    that the substrate can reason about + manipulate. The reflective step
    is a substrate operation, not a syntactic one.
  · Applying order-N to itself (the abstraction axis) is the next rung of
    the reflective tower. Each application creates a new level.

**Where the substrate already gestures at this:**
`mlir_dialect`, `intermediate_representation`, `higher_order_logic`,
`mlir`. The Mt naming IR is the agent's existing recognition that a
function reified-as-data is a useful object.

---

### 2. Michie, D. (1968) — "Memo" Functions and Machine Learning

**Architectural commitment:** A function caches its OWN outputs by input.
The cache is a property of the function (not of the call site, not of the
runtime). The function carries its memo table. This is the original
function-level cache pattern; later AD work (Pearlmutter, Siskind 2008
"Reverse-Mode AD in a Functional Framework"; JAX/Autograd) inherits this
exactly.

**What it constrains in the pivot:**
  · `cached_shape` is the function's MEMO TABLE for its shape, not for
    its outputs. The function holds its shape the way a memo function
    holds its output cache.
  · Cache identity is structural — Michie keyed by input tuple; the
    substrate keys by Term-tree structural hash. Same pattern, different
    granularity.
  · The Mt's `memoisation_eliminates_redundant_recomputation` IS Michie's
    principle — the agent already holds the source.

---

### 3. Cousot, P. & Cousot, R. (1977) — Abstract Interpretation: A Unified Lattice Model for Static Analysis

**Architectural commitment:** A program is analyzed in an ABSTRACT DOMAIN
that approximates its concrete semantics. The abstract semantics IS the
shape — what the program does WITHOUT committing to specific values. The
abstraction lattice gives a soundness story (abstract value over-approximates
all concrete behaviors).

**What it constrains in the pivot:**
  · `function_shape` is the abstract interpretation of a Term-tree.
    Concrete semantics = what evaluation produces on a specific input.
    Abstract semantics = what evaluation produces over ALL inputs.
    Shape = the abstract semantics.
  · Negative problem space pruning = abstract-domain-based pruning:
    when the abstract value of a candidate excludes the target's abstract
    value, prune. This is what AI's program analysis literature calls
    "soundness without completeness."
  · Order-N over functions is a transfer function in the abstract domain.

**Where the substrate already gestures at this:**
The substrate's existing `referential_transparency`,
`extensional_equivalence`, `cost_equivalence` soundness categories (in
`compiler_theory`) are abstract-interpretation soundness commitments
already. The agent has the lattice; function_shape sits inside it.

---

### 4. Pearlmutter, B. & Siskind, J. (2007–2008) — Higher-Order Forward + Reverse Mode AD

**Architectural commitment:** The DERIVATIVE OPERATOR is itself a function:
it takes functions to functions. n-th order derivative = derivative
composed with itself n times. The derivative tree is CACHED across the
program — forward-mode AD attaches tangent values, reverse-mode caches
adjoints. The whole "differentiable programming" paradigm (JAX, PyTorch
autograd, Julia's Zygote) inherits this.

**What it constrains in the pivot:**
  · `order_n_axis` is not a property of a value-over-a-dimension; it is
    a property of a FUNCTION, manifesting as the function's behavior under
    repeated application of the derivative operator.
  · Applying the operator to itself (the abstraction case) is what AD
    libraries call "higher-order AD" — well-studied, well-implemented.
    Pearlmutter & Siskind's "Lazy Multivariate Higher-Order Forward-Mode
    AD" gives the formal account.
  · `cached_shape` = the cached derivative tree. AD does this in practice.

**Where the substrate already gestures at this:**
`order_n_concepts` over signals + the existing `nth_order_terms` builder.
The lift from signals to functions is the AD lift.

---

### 5. Nelson, T. & Narens, L. (1990) — Metamemory: A Theoretical Framework and New Findings

**Architectural commitment:** Metacognition is a two-level model. There
is an OBJECT level (where cognition happens) and a META level (where
cognition is monitored + controlled). Two channels connect them:
**MONITORING** (object → meta: the meta level reads the object level)
and **CONTROL** (meta → object: the meta level changes the object level).
Subsequent work (Koriat, Bjork, Dunlosky) extends this to specific
metacognitive judgments (judgment of learning, feeling of knowing,
remember/know).

**What it constrains in the pivot:**
  · Shape assessment IS the monitoring channel. The meta level reads
    the object-level function and produces a shape descriptor.
  · Using shape to decide which function to apply IS the control channel.
    Negative problem space pruning is meta-level control over which
    object-level evaluations even start.
  · The three classification axes (recursion, order-N, abstraction) are
    monitoring outputs. The substrate's existing `feedback_control` Mt
    (composition_topology layer, commit 486f65e) already has the
    monitoring+control vocabulary at the runtime level. Nelson-Narens
    lifts it to cognition.

**Where the substrate already gestures at this:**
`feedback_control`, `higher_order_theory_consciousness`, the substrate's
own L6 essential variable monitor (runtime-level monitoring). The
metacognition vocabulary the agent already holds maps directly.

---

## What this narrowing tells us

Each of the pivot's three needs has a specific named source:

| pivot need                        | grounded by                                |
|-----------------------------------|--------------------------------------------|
| Cache higher-order shapes         | Michie 1968 + Pearlmutter-Siskind 2008 AD  |
| Generic order-N                   | Pearlmutter-Siskind AD + Smith 3-LISP      |
| Classify functions                | Cousot abstract interpretation + Nelson-Narens monitoring |

**Each commitment is concrete:**
  · `function_shape` = abstract interpretation of a Term-tree (Cousot)
  · `cached_shape` = function-level memo table (Michie) carrying the
    function's reified abstract semantics
  · `meta_shape` = the next level of the reflective tower (Smith) reached
    by applying the derivative operator to the function (Pearlmutter-Siskind)
  · `recursion_axis`, `order_n_axis`, `abstraction_axis` = monitoring
    outputs (Nelson-Narens) over fixed-point structure, AD-order, and
    reflective-tower-rung respectively
  · `negative_problem_space_pruning` = abstract-domain pruning (Cousot)
    + meta-level control (Nelson-Narens)
  · `shape_keyed_lookup` = the memo function's cache hit (Michie)

The vocabulary's role becomes: name the agent's SPECIFIC INSTANTIATION
of each of these established mechanisms. Each function_shape concept
inherits semantics from a named paper; the substrate's data + the
literature jointly constrain the architecture, instead of either alone.

---

## What this narrows OUT

  · "Should Shape be hash-keyed or id-keyed?" — Michie says the function
    carries its memo table; structural-hash keying is the standard
    extension. (NOT a free choice; AD's gensym / object-identity keying
    is the precedent.)
  · "Should assessment run as a Rule or a pass?" — Nelson-Narens monitoring
    is CONTINUOUS, not triggered. The rule model is closer.
  · "What's the Rust node type's layout?" — Cousot's abstract-domain
    lattice tells us: the layout must support the join/meet operations
    of the lattice. Not arbitrary.

The remaining choices are no longer "design space wide open" but
"choose within the cited theory's commitments."

---

## What to do with this

The narrowed vocabulary extension would:
  · Augment each function_shape concept with a `cites_prior_work` field
    naming the source (Smith 1982; Michie 1968; Cousot & Cousot 1977;
    Pearlmutter & Siskind 2007–8; Nelson & Narens 1990).
  · Add 5 new concepts naming the inherited mechanisms directly:
    `abstract_interpretation`, `memo_function`, `reflective_tower`,
    `derivative_as_higher_order_function`, `monitoring_and_control_channels`.
  · Add bridge rules naming that function_shape's mechanisms are the
    agent's instantiation of these prior-work patterns.

Whether to do this — and which lineages to commit to — is the next
decision. The narrowing happens here; the seed extension only after
the user picks the lineages to inherit from.

---

## Sources

  · Brian C. Smith. "Reflection and Semantics in a Procedural Programming
    Language." MIT TR-272, 1982. + "Reflection and Semantics in LISP."
    POPL 1984.
  · Donald Michie. "'Memo' Functions and Machine Learning." Nature
    218:19–22, 1968.
  · Patrick Cousot & Radhia Cousot. "Abstract Interpretation: A Unified
    Lattice Model for Static Analysis of Programs by Construction or
    Approximation of Fixpoints." POPL 1977.
  · Barak A. Pearlmutter & Jeffrey Mark Siskind. "Lazy Multivariate
    Higher-Order Forward-Mode AD." POPL 2007. + "Reverse-Mode AD in a
    Functional Framework." TOPLAS 2008.
  · Thomas O. Nelson & Louis Narens. "Metamemory: A Theoretical Framework
    and New Findings." The Psychology of Learning and Motivation 26:125,
    1990.
