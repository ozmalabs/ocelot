# A theory as a held solution shape — falsifier run, 2026-08-25

**Question.** *A theory is a solution shape you try to produce.* Can a TARGET shape live in the
codebook `ShapeDecode` already reads — so that an unmet goal becomes a decodable residual rather
than a boolean?

Run in a detached worktree with its own engine (`8afcc77b2766`, provenance 10/10), because the live
tree's installed `.so` had been replaced without its build record and provenance correctly refused
to measure.

## What was already true, and why it is not the answer

`compose_design_for_goal(substrate, goal_signature, ...)` already decodes a goal against held parts
and returns a residual. But the shape arrives **as a Python argument** — computed by a caller, used
once, discarded. No want-node holds one. Measured across the tree: a `Goal` is
`{kind, status, source, verified, predicate, concept, objective, label}` — a kind-tag plus a
pointer, over 46 minting sites; `SelfConcern` 26 sites; `Hypothesis` 4. Nothing says what the wanted
state looks like.

## Three arms, all positive

**1. A target decodes against held parts, and the residual is the work remaining.**

Codebook: three `ShapeSignature` parts with `kind: "capability"` — a grain invented for this test,
which is itself the point.

| arm | covered | residual |
|---|---|---|
| fully covered | 4 | `[]` |
| partly covered | 2 | `[["has","airframe","radar"]]` |
| needs an unheld part | 0 | both relations |

The decode also returns a PLAN — `ordered_parts`, per-step `part` / `shape_fit` / `covers` / `why`.

**2. The shape can be HELD on a node and decoded BY A RULE.** A `Theory` node carrying its own
`signature`, a rule reading `Attr(th, "signature")` into `ShapeDecode`, no Python deciding anything.
Settled in 1 step, residuals identical to arm 1.

**3. The loop CLOSES at the target grain.** residual → mint a part → epoch bump re-arms the decode →
re-decode covers. Codebook 1 → 2 parts, `covered_count` 2, residual `[]`, 3 steps.

**So the engine prevents none of this.** Grain-agnosticism is now confirmed empirically rather than
by reading the loader: `kind: "capability"` needed no change anywhere. The gap is only that **no
seed writes a shape onto a want-node.**

## The caveat that matters more than the result

**Arm 3 closes the loop mechanically, and its semantics are wrong as written.** Minting the residual
turns *"my theory needs radar"* into *"radar is a held capability"* — the loop reports `covered` and
`residual: []` while nothing was built and nothing was learned. That is **wishful thinking with a
green light on it.**

The asymmetry is exact and worth stating:

* at the OBSERVATION grain, a residual is EVIDENCE. The signal really did contain something the
  codebook could not explain, so minting a quantum is warranted — the world supplied it;
* at the TARGET grain, a residual is a DEMAND. Nothing supplied it. Minting it asserts a capability
  on the strength of wanting one.

So a mint at the target grain must be gated on something the observation grain gets for free:
evidence that the part was actually produced. The natural gate already exists in this tree — the
`Experiment → judge → adopt` path, and the human-gated `SelfConcern → StandingConcern` promote — and
the honest reading is that **a target-grain residual should open a concern, not close one.**

That is a design conclusion this experiment supports but does not test.

## What this does NOT establish

* **Where a real theory's shape comes from.** The relation vocabulary here (`has(airframe, wing)`)
  was authored by hand. At the observation grain a shape falls out of quantizing a signal; at the
  target grain someone must author or derive it, and nothing here addresses that. It is the hard
  half.
* **That any existing goal can be given a shape.** 46 `Goal` sites carry kind-tags; converting even
  one is untested.
* **Any benchmark value.** Three synthetic arms with a hand-made vocabulary. Synthetic-proven
  mechanism is not benchmark value, and this is the former.


## Built: `seeds/theory_residual_concern.json` (v1.0.0)

The design conclusion above is now a seed, three rules, and the shape of it is the asymmetry:

* `tr_decode_theory` — decode the theory's OWN held signature against the codebook, epoch-gated on
  the same `codebook_epoch` idiom the sd loop uses, so the decode re-arms whenever the codebook
  grows;
* `tr_open_concern` — a non-empty residual mints a `SelfConcern{kind: capability_gap, content: <the
  residual>}` on the existing human-gated spine (promote → `StandingConcern` → experiment → adopt),
  content-deduped against every live concern exactly as `gap_awareness` does. It does NOT mint the
  missing part;
* `tr_resolve_concern` — the concern closes when the residual has genuinely emptied. **Nothing in
  this seed can empty a residual.** This rule only observes that one has emptied, and that
  asymmetry is the entire point.

**Gated, 5/5, and mutation-tested — including the mutation that matters.** Removing any of the three
rules turns something red (4 / 4 / 1). And re-adding the wishful mint as a fourth rule turns **3
red, including `test_the_theory_does_NOT_become_reachable_by_wanting_it`** — so the negative control
demonstrably detects the failure it exists to prevent, rather than passing because nothing ever
happens. `test_the_concern_resolves_only_when_the_part_IS_genuinely_held` is its positive control:
without it, "the concern never closes" would pass trivially for a seed that closes nothing.

Adjacent and NOT the same thing: `seeds/goal_residuals.json` holds `GoalResidual` records of
MEASURED CEILINGS — refuted seams, so a goal-selection collapse cannot re-propose one. Its
`sig_seam` / `sig_lever` / `sig_target` are identifier tags, not shape signatures. It remembers what
was refuted; this seed measures what is not yet reachable.

**Still not established** (unchanged from above): where a real theory's shape comes from. The
relation vocabulary here is authored by hand, and converting any of the 46 existing `Goal` sites to
carry a shape is untested. That is the hard half and this seed does not touch it.


## Where a theory's shape comes from — shape math, and the frame is measurable

The gap left open above ("where does a real theory's shape come from") has an answer that is not
"someone authors it": **you pick a starting point you already hold and iterate it against everything
through order N.** A problem adjacent to one you hold is easy; a problem you have no reference frame
for is intractable.

That makes tractability a DISTANCE, and the distance is directly measurable with the algebra already
in `term.rs`. Anti-unify the target against each held shape and read the SPECIFICITY of the least
general generalisation — the fraction of leaf positions the lgg pins rather than leaving WILD. An
all-WILD lgg means nothing is shared: no frame.

Held: `wing = [has(airframe,wing), controls(aileron,wing)]`,
`engine = [has(airframe,engine), controls(throttle,engine)]`.

| target | lgg specificity | verdict |
|---|---|---|
| `radar` — same two-relation shape | **0.50** | derivable; template `[has(airframe,·?·), controls(·?·,·?·)]` |
| `gear` — one relation, shares `has(airframe,·)` | **0.67** | derivable |
| `proof` — different predicates AND arity | **0.00** | **no reference frame** |

The separation is sharp — 0.50/0.67 against 0.00, nothing between — and it lands where the framing
predicts: the alien target has no frame, and the two adjacent ones do, with `gear` (which shares
more of the one relation it has) scoring HIGHER than `radar`.

### The operational finding: iterate over PARTS, not whole shapes

**The first run of this got `gear` wrong, and the way it got it wrong is the useful part.**
Anti-unifying whole SIGNATURES, `gear` scored 0.00 — reported as intractable — because it carries one
relation where `wing` carries two, and differing arity collapses the entire lgg to WILD. That
conflates *"different length"* with *"nothing shared"*.

Aligning relation-to-relation instead — each target relation against its best-matching held relation
— moves `gear` from 0.00 to 0.67 while leaving `proof` at 0.00 and `radar` unchanged. So:

> **"Iterate it against anything and everything" has to mean iterating over PARTS.** Whole-shape
> anti-unification produces FALSE INTRACTABILITY: a problem you have a perfectly good frame for
> reads as unreachable purely because it is a different size. An agent using the whole-shape form
> would abandon tractable problems and never learn why.

That is a failure mode worth naming, because it is silent — an all-WILD lgg looks exactly like a
genuinely alien problem.

### Not established

* **Order N.** Only order 1 was measured — one transform from one held shape. Composing transforms
  (adjacent-to-adjacent-to-target) is untested, and it is what "through order N" actually means.
* **The threshold.** 0.3 was used to print a verdict; the measured gap is 0.50/0.67 vs 0.00, so
  nothing here fixes where the line sits, and on this tree's own standing rule a bare threshold is a
  number standing where a shape belongs.
* **Scale.** Three targets, two held shapes, a hand-made vocabulary. Synthetic-proven mechanism, not
  benchmark value.


## Order N of M of O — the closure, and which operators stay inside it

Order N is not a ladder. A theory's shape lives in the CLOSURE of what you hold under the shape
algebra, and the operators branch, so the reachable set is countably infinite: you hold GENERATORS
and a frontier, never the set. That is this tree's own extensive/ℕ direction — *"there is always one
more step outward"*, stored as the finite explored part plus the fact that it does not end.

**The branching is real.** From three held shapes, expanding by every pairwise anti-unification
template, every witness substitution, and every unification:

| order | new | total distinct |
|---|---|---|
| 0 | 3 | 3 |
| 1 | 5 | 8 |
| 2 | 17 | 25 |
| 3 | **157** | **182** |

— and that is with the frontier capped at 24 per step, so the true branching is higher.

### The finding: only the MEET direction closes over the shape space

"Combine in countably infinite ways" presumes the combinations are themselves combinable. Measured
by leaf type:

| operator | leaf types out | closes? |
|---|---|---|
| `AntiUnify` | `['str']` | **yes** |
| `AntiUnifyWitness` → template | `['str']` | **yes** |
| `Unify` | `['frozenset', 'str']` | **NO** |

`Unify` places a `frozenset({'wing','engine'})` at every position where the inputs disagree
concretely. That is defensible as semantics — it means *either* — but it is not a signature, and a
plain shape has no frozenset leaves anywhere. **So feeding a `Unify` result back into the algebra is
not iteration, it is drift**: the JOIN's codomain is strictly richer than the MEET's.

The practical consequence is that the iterable closure — the one whose members can serve as the next
step's inputs — is generated by anti-unification and substitution. The join direction can be used to
BLEND, but not to compose repeatedly.

### What I failed to measure, and why it is worth recording

**Whether specificity ORDERS the search: inconclusive.** Since the closure is not enumerable, the
only thing that makes a deep target reachable is expansion order, and best-first on lgg-specificity
is the obvious candidate. Two attempts, both bad:

* targets drawn from orders 1–2 were found in 1–2 expansions by BOTH blind and guided search — no
  headroom to discriminate;
* targets drawn from order 3 were found by NEITHER within a 120-expansion budget — and the reason
  is the finding above. Those targets were `Unify` artifacts riddled with frozensets, so whether
  they are "reachable" depends on the exact expansion path that produced them. The comparison was
  ill-posed, not merely underpowered.

Doing it properly needs targets that are well-defined independently of the path that found them —
i.e. drawn from the anti-unify/substitute closure only, with `Unify` excluded from the expansion.
That is a straightforward redesign and it is not done here.

So: the closure is real and it branches hard; the MEET direction is the part that iterates; and
whether the specificity gradient tames the search is **still open**.


## The redesign: Unify excluded — and the composition closure turns out to be FINITE

Expanding by anti-unification and substitution ONLY (no `Unify`, which does not close over the
space) makes the closure well-defined. It also answers a question the earlier run could not ask.

**The MEET-only closure SATURATES, immediately, on every held set tried:**

| held set | generators | closure | layer sizes |
|---|---|---|---|
| 3 regular (same 2-relation shape) | 3 | 5 | [3, 2, 0] |
| 5 regular | 5 | 7 | [5, 2, 0] |
| mixed arity (1, 2, 3 relations) | 3 | 4 | [3, 1, 0] |
| heterogeneous predicates | 3 | 4 | [3, 1, 0] |
| deep nesting | 2 | 3 | [2, 1, 0] |

Every one saturates at **order 2**, with a closure of about *generators + 2*. That is not an
artifact of a regular corpus — it holds across arity, predicate vocabulary and nesting depth, and it
is explicable: anti-unification GENERALISES, and generalisation converges (`lgg(lgg(a,b), c)` is
just `lgg(a,b,c)`).

**So composition is not where the countable infinity is.** Composing what you hold gets you a
handful of templates and then stops.

## Where the infinity actually is, and why "no frame" is intractable rather than slow

The infinity is in INSTANTIATION. A template with WILDs admits a binding for every term there is,
and those terms can themselves be instantiated templates. That splits the search into two halves
that could not be more different:

* choosing a **TEMPLATE** — finite, tiny (≈ k+2), and rankable by lgg specificity;
* choosing a **BINDING** — countably infinite.

And the second half is not searched at all, because **the target determines it**. Composed
in-engine — `Substitute(template = AntiUnifyWitness(t, target)[0], sigma = …[1][1])` — the target is
reconstructed exactly.

**But reconstruction is NOT the signal, and this is the correction that matters.** It succeeds for
an ALIEN target too. In the worst case the lgg collapses to `WILD` and the sigma carries the whole
target, so `Substitute` rebuilds it either way. Success proves nothing.

What differs is the SPLIT — an MDL question, not a success/failure one:

| target | leaves | template pins | binding must carry | explained by the frame |
|---|---|---|---|---|
| real (`radar`) | 6 | 3 | 3 | **50%** |
| alien (`proof`) | 6 | **0** | **6** | **0%** |

**A frame is what lets the template carry the load.** With none, the binding is the entire answer —
you have reconstructed the target *from itself*, learned nothing, and the "derivation" is a tautology.
That is why *no reference frame* is intractable rather than merely slow: not that the search is
long, but that **every candidate answer is as expensive as the question**, so there is no gradient to
descend.

### Consequences for the search, and what remains open

The specificity gradient operates on the FINITE half — template choice — which is a much weaker
claim than "it tames a countably infinite search", and a much more tractable one. Whether ranking
templates by specificity beats picking arbitrarily is **still not measured**; with closures of size
4–7 it may not matter at all, and the honest expectation is that it does not.

Also unmeasured: whether MINTING (which adds a generator, and so multiplies the closure) is where
practical reach actually comes from. The saturation result points that way — a fixed codebook's
compositional reach is ~k+2 shapes — but nothing here tests it.

### An incidental engine finding

`AntiUnifyWitness`'s sigmas are keyed by position-PATH tuples, so they **cannot cross the Python
JSON boundary** back into `Substitute` (`TypeError: keys must be str, int, float, bool or None, not
tuple`). The two Terms compose only when nested so the sigma never leaves the engine — which is how
a rule would express it anyway, but it means no Python shim can pass a witness between them.
