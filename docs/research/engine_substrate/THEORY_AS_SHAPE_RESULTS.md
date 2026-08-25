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
