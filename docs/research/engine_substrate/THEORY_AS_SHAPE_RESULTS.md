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
