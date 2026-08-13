# Identity-feedback: writing `identity_field` from the evidence render — PREREG

Base `main @ d80682d` ("Merge can-external-field-decay: native external_field
decay, closes `maybe_decay_h`, GO"), verified via `git log --oneline -1 main`
before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-identity-feedback`, branch
`can-identity-feedback`.

This is the closing rung of today's CAN arc. It builds the ONE thing every
prior rung in the arc named and explicitly declined to build: a native rule
that WRITES `identity_field` from the identity-evidence log-odds reading
(`can_native_identity_evidence_sample`'s own render, `seeds/
can_decay_identity.json`), so `can_native_update_3state`/`_2state`'s own
local-field sum (which already READS `identity_field` six times,
`seeds/can_native_reimplementation.json:166,250,350,434,566,652`) actually
feels it. This closes `maybe_update_identity`, and investigates whether
`nudge_identity_on_flipped` closes too.

---

## 1. What already exists (read before designing anything new)

- **The reading half is built and proven**
  (`CAN_DECAY_IDENTITY_RESULTS.md` §2, §4b): `can_native_identity_evidence_
  sample` accumulates a per-Concept `identity_evidence_confirm`/
  `identity_evidence_disconfirm` ledger, one +1 per tick a nonzero σ is
  sampled (sign-gated), policy-gated the same `allow_h_drift` axis every
  rule in this seed uses. The graded reading is the non-materializing Term
  `Log(Div(Plus(confirm,1), Plus(disconfirm,1)))` — evaluated live, NEVER
  written back to any attr by any existing rule. Measured live: 10
  consecutive confirms → `2.3979`; a 5/5 flip-flip split → EXACTLY `0.0`.
- **The consuming formula** (`can_native_update_3state`/`_2state`,
  `seeds/can_native_reimplementation.json:143-221` and the mirrored `_2state`
  block): `target = IfThenElse(Gt((external_field + identity_field +
  Sum(weight*neighbour_state)) * temperature, ATANH_HALF), 1, IfThenElse(Lt(...,
  -ATANH_HALF), -1, 0))`. `identity_field` is READ as a materialized float
  bias term, structurally identical to `external_field`'s own role in the
  same sum — confirmed by direct read, not assumed (both appear inside the
  exact same `Plus` subtree, `:150-159`/`:234-243`).
- **The closest structural template, `can_native_external_field_decay`**
  (`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` §1, `seeds/can_decay_identity.json`
  local rule, quoted verbatim from source): epoch-gated
  (`Gt(mt.can_tick, c.external_field_decay_tick)`), policy-gated (the
  byte-identical `Or(update_policy==adaptive, And(update_policy==hybrid,
  Not(allow_h_drift==0)))` subtree), symmetric clamp toward zero via `Max`/
  `Min` (`max(h-1,0)` when positive, `min(h+1,0)` when negative), own epoch
  attr never shared with sibling rules. This is a decay-toward-zero shape —
  our new rule needs a DIFFERENT target (toward the CURRENT evidence sign,
  not toward zero unconditionally), so it transfers the MACHINERY (epoch
  gate, policy gate, `Max`/`Min` clamp idiom, own epoch attr) but not the
  literal target.
- **The continuous target behaviour to match, not transliterate**
  (`can_ops.rs:774-797`, `update_identity_dynamics`): `identity_field ←
  identity_field + α·σ - β·identity_field` — a leaky integrator. Docstring,
  quoted: *"Sustained positive σ → identity grows positive... Flipping σ
  averages to near zero → identity decays toward zero... identity is never
  frozen — without being reinforced, it fades."*

---

## 2. The design decision — registered BEFORE any code is written

### 2.1 Direction: fixed 1-quantum step toward the SIGN of the current
identity log-odds render

Each tick this rule is eligible (own epoch gate, below), `identity_field`
moves by exactly **one quantum** in the direction the CURRENT
`identity_evidence_confirm`/`_disconfirm` log-odds render implies:

```
logodds = Log(Div(Plus(confirm,1), Plus(disconfirm,1)))
identity_field ←
  IfThenElse(Gt(logodds, 0), identity_field + 1,
    IfThenElse(Lt(logodds, 0), identity_field - 1,
      # logodds == 0 (neutral / flip-flop): decay toward zero,
      # the SAME symmetric clamp can_native_external_field_decay uses
      IfThenElse(Gt(identity_field, 0), max(identity_field - 1, 0),
        IfThenElse(Lt(identity_field, 0), min(identity_field + 1, 0),
          identity_field))))
```

This is the SAME fixed-quantum-step shape both existing decay rules already
use (`CAN_DECAY_IDENTITY_RESULTS.md` §1, `CAN_EXTERNAL_FIELD_DECAY_RESULTS.md`
§1) — no new scalar rate is introduced; the quantum is the SAME `1` every
other rule in this seed steps by. The neutral branch reuses the EXACT
`Max`/`Min` clamp-toward-zero subtree `can_native_external_field_decay`
already built, giving the "flips average to zero → identity decays"
behaviour for free, on the SAME shape.

### 2.2 Rejected alternative: step size scaled by the render's own magnitude

The task explicitly asks to investigate reusing the render's own MAGNITUDE
(not just sign) as the step size, since `ln(confirm+1)` already gives
diminishing-returns scaling "for free" (`CAN_DECAY_IDENTITY_RESULTS.md`
§4c measured this: marginal gain per additional recurrence shrinks from
`0.2747` (n:1→5) to `0.0835` (n:5→20)).

**Investigated and REJECTED, for a stability reason specific to this rung's
own risk, not a style preference.** A magnitude-scaled step means the
PER-TICK JUMP in `identity_field` — the quantity that directly enters
`can_native_update_3state`'s own threshold comparison — GROWS every tick
sustained evidence continues (from `ln(2)≈0.69` at confirm=1 to `ln(11)≈2.40`
at confirm=10, unbounded upward). A per-tick step that grows in size is
exactly the shape a Lyapunov/energy argument needs to NOT have — the
existing discrete-async convergence guarantee
(`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2: "every committed flip strictly
decreases a bounded energy function... a period-2 cycle is mathematically
impossible BY THE SHAPE OF THE UPDATE") relies on individual node flips
being the only source of state change; a bias term that can jump by
increasingly large amounts is a new, unbounded-step external perturbation to
that argument, and threatens it in a way a small worst-case, FIXED,
one-quantum-per-tick perturbation does not. **Fixed quantum wins on
stability grounds, checked directly against this rung's own single most
important risk (§4/§5 convergence check), not assumed a priori.**

### 2.3 Rejected alternative: recurrence-modulated step (mirroring
`nudge_identity_on_flipped`'s own `α_eff = base·(1+ln(recurrence))`)

Same reasoning as §2.2 applies identically — modulating the STEP size by
any monotonically-growing count (recurrence or evidence-count alike)
reproduces the same unbounded-per-tick-jump risk. Rejected for the same
reason. The diminishing-returns property the render already gives "for
free" (§4c of the reading-half rung) shows up correctly in this design
anyway, but at the SIGN-STABILITY layer, not the step-size layer: once
`confirm` is large relative to `disconfirm`, log-odds stays solidly
positive and a large SWING of opposite evidence is needed to flip its sign
(hysteresis) — exactly the qualitative "committed identity is hard to
dislodge" property wanted, achieved without ever varying the per-tick jump
size.

### 2.4 Boundedness — reported honestly, not solved by inventing a cap

Under LITERALLY sustained single-direction evidence forever, this design's
`identity_field` grows by exactly 1 every eligible tick, unboundedly in the
limit — there is no `-β·identity_field` decay term counteracting sustained
reinforcement (unlike the continuous leaky integrator, which converges to a
steady state ≈ α/β under sustained σ). **This is registered explicitly, not
smoothed over**: this mirrors `evidence_confirm`'s OWN existing design
exactly (it too grows unboundedly under sustained reinforcement, with no
cap — `CAN_DECAY_IDENTITY_RESULTS.md` §4a's own 5-tick trajectory keeps
climbing with no ceiling in the rule itself). No new cap constant is
introduced here, per the standing `CLAUDE.md` "SHAPES, NOT NUMBERS" rule —
inventing a bound value with no existing precedent in this seed family would
itself be exactly the "unpaid debt" scalar knob that rule warns against.
Within any FINITE observed run (the live demonstrations, §5 below;
real-world ticks are always finite), the magnitude is of course bounded —
this is reported precisely as "bounded within any tested/finite window, not
capped by construction," which is the honest, weaker claim this design
actually supports.

### 2.5 Epoch gate — own attr, independent schedule

Own epoch attr `identity_field_tick` (mirrors `identity_decay_tick`'s own
independence from `identity_evidence_tick`, `CAN_DECAY_IDENTITY_RESULTS.md`
§5 point 3): `Gt(mt.can_tick, c.identity_field_tick)`. **No same-tick-race
guard against `can_native_identity_evidence_sample`** — registered
prediction, checked against source before writing the rule (§3 confirms):
the new rule only READS `identity_evidence_confirm`/`_disconfirm` (never
writes them) and only WRITES `identity_field`/`identity_field_tick` (which
no other rule reads or writes) — there is no shared mutation target for a
same-tick race to occur over, structurally different from the
`can_native_evidence_decay` race `CAN_DECAY_IDENTITY_RESULTS.md` §3 found
and fixed (that race was between two rules WRITING THE SAME counter in
opposite directions).

### 2.6 Policy gate

The BYTE-IDENTICAL `Or(update_policy==adaptive, And(update_policy==hybrid,
Not(allow_h_drift==0)))` subtree every other rule in this seed uses — the
SAME axis `maybe_update_identity`'s own continuous path checks
(`mt_allows(substrate, mt, "allow_h_drift")`).

---

## 3. Same-tick-race check — registered prediction, to be confirmed by grep
before the rule is built

**Prediction**: `identity_field` currently has ZERO writers anywhere in
either native seed (confirmed by the SAME class of grep
`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` §0 ran for `external_field`) —
`identity_field` only ever appears inside `can_native_update_3state`/
`_2state`'s own READ-side local-field sum. If true, this new rule is the
FIRST writer, exactly mirroring `external_field`'s own situation, and no
same-tick-race guard beyond the epoch gate is needed. To be confirmed live
in the RESULTS doc by direct grep, not assumed.

---

## 4. The convergence-validation plan — the single most important check in
this rung, registered before any result is seen

### 4.1 What could go wrong, named precisely

`identity_field` feeds directly into the SAME local-field sum
`external_field` and neighbour couplings feed into, which
`can_native_update_3state`/`_2state`'s discrete-asynchronous update has a
PROVEN convergence guarantee for (0/20 non-convergent draws per condition,
`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2) — a guarantee that holds
because every committed flip strictly decreases a bounded energy function,
UNDER A FIXED bias configuration during a settle. This rung introduces a
NEW rule that changes one component of that bias (`identity_field`) WHILE
the discrete update is also running inside the SAME `run_rules` fixpoint —
if `identity_field` changes are interleaved with state flips in a way that
lets a Concept's local field cross the threshold back and forth as
`identity_field` itself moves, the Lyapunov argument (built for a fixed
bias) no longer straightforwardly applies, and genuine non-convergence
(the discrete update never reaching a fixpoint within a bounded step count)
becomes a live possibility, not merely a theoretical curiosity.

### 4.2 The scenario — reusing `test_can_native_reimplementation.py`'s own
construction, unmodified

`_build_draw` (N=8 complete graph, symmetric `causal_influence` edge pairs,
`external_field` drawn `Uniform(-1,1)`, `causal_influence.weight` drawn
`Uniform(-1,1)` then rounded to a coarse (3-level) or fine (9-level)
vocabulary) — reused byte-identically, with ONE addition: the substrate for
this rung's convergence test loads BOTH `seeds/can_native_reimplementation.
json` AND `seeds/can_decay_identity.json` (the new rule's home), so the new
identity-feedback rule is live in the SAME `run_rules` fixpoint as
`can_native_update_3state`/`_2state`. `identity_field` starts at `0.0`
(matching `_build_draw`'s own existing initialisation) and
`identity_evidence_confirm`/`_disconfirm` start absent (read as 0 by
`Plus`).

**One necessary addition beyond a single `run_rules()` call**: because the
identity-evidence ledger only accumulates from SAMPLED σ (which requires
`state != 0`, itself only reachable once the discrete update has committed
at least once), a single-tick draw would let the feedback rule fire at most
once or twice before the ledger has any real signal. The convergence test
therefore drives `can_tick` forward across MULTIPLE ticks per draw (mirrors
`_reinforce_hebbian_pair`'s own multi-tick drive pattern,
`tests/test_can_decay_identity.py:102-111`), calling `run_rules()` at each
tick, so the identity-feedback rule gets multiple real opportunities to
perturb `identity_field` while the discrete update is also live — this is
the scenario that actually exercises the risk named in §4.1, not a
diminished one.

### 4.3 Sample size and GO/NO-GO criterion, registered before running

**60 real draws** — 30 coarse + 30 fine (`N_DRAWS=30` per vocabulary
condition), mirroring the "0/60 non-convergent draws" figure
`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s own PoC used as this arc's
precedent for "proven, not assumed" convergence — run for **`discrete_mode
="3state"`** (the deadzone case named as the higher theoretical risk,
`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`'s own §5.1 gap) as the primary,
headline number. As a secondary check (not the primary claim, reported
honestly either way), the SAME 60-draw sweep is also run for
`discrete_mode="2state"`, since `identity_field` is read by BOTH rules
(`seeds/can_native_reimplementation.json` lines 166/250 belong to the
3-state rule; 434/566/652 span the 2-state rule and its own mirrored
block) — 120 real draws total across both modes.

**GO**: `0/60` (3-state) non-convergent (each draw's `run_rules(3000)`
reaches a fixpoint, `steps < 3000`, at EVERY tick of the multi-tick drive,
not just the final one) — matching the EXACT zero-tolerance bar this arc's
own precedent set (`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2 registered
and met the identical bar for the undisturbed rule). Any non-zero count is
NOT automatically a NO-GO on the whole rung — per the task's own explicit
instruction, a non-zero count triggers a targeted investigation (does a
specific tick/step-size/recurrence pattern cause it; does further bounding
resolve it) BEFORE any GO/NO-GO verdict is written, and if no principled
fix closes it within this rung's scope, the honest verdict is NO-GO on
`maybe_update_identity`'s native migration specifically — reported
precisely, not forced.

### 4.4 Two-Mt isolation, unchanged check

Reuse `test_can_mt_scoped_consumers.py`'s own `_isolated_pair` pattern
(strong equal external fields, `discrete_mode="3state"`) with a SECOND,
untouched sibling Mt in the same graph — confirm the new rule, reached
through `scoped_settle`, never perturbs the sibling Mt's `identity_field`
or `state`, matching every prior native rung's own isolation guarantee.

---

## 5. Live demonstrations required (registered, before building)

(a) Consistent σ (`state=+1.0` held for many ticks, `discrete_mode="static"`
so the discrete update is inert and `identity_field`'s trajectory is
observed in isolation from the update rule — the SAME isolation
`test_identity_evidence_consistent_state_reads_stronger_than_flipping_state`
already uses): `identity_field` must move in ONE consistent direction
(same sign every step it changes), growing in magnitude across ticks, never
negative, never exceeding what the fixed-quantum step count over N ticks
allows (an explicit, checkable numeric bound for THIS finite run, per §2.4's
honest framing).

(b) Flip-flopping σ, same isolation: `identity_field` must end at or very
near zero — mirroring `can_ops.rs:774`'s own docstring, "flips average to
zero → identity decays toward zero," via the neutral-branch decay-toward-
zero clamp (§2.1).

(c) The §4 convergence sweep, real numbers, both modes.

(d) Two-Mt isolation (§4.4) with identity-feedback active.

---

## 6. Wiring plan for `maybe_update_identity`/`nudge_identity_on_flipped`

`maybe_update_identity`: mirror `maybe_decay_h`'s exact pattern —
`if _is_native(substrate, mt): from domains.can_native_orchestration import
scoped_settle; return scoped_settle(substrate, mt)`, else the byte-unchanged
continuous branch. Registered expectation: this migrates cleanly, since the
new rule is gated + gated exactly like every other native rule reached via
`scoped_settle`.

`nudge_identity_on_flipped`: registered as GENUINELY OPEN, to be decided
during the build, not pre-committed. The function is EVENT-triggered (fires
once, immediately, on insight consolidation, targeting SPECIFIC flipped
node ids with an insight-supplied `target_sigma` and a `recurrence_count`
-scaled `alpha_eff`), while the new native rule is a per-tick, epoch-gated,
whole-Mt sample step with NO event/target-sigma/recurrence input surface —
a different temporal grain and a different input shape. If no clean native
mapping is found (most likely outcome, given §2.2/§2.3's rejection of any
recurrence/magnitude-scaled step — the exact mechanism this function would
need), this function stays on the continuous path, reported as an honest,
specific finding, per the task's own explicit permission to do so.

---

## 7. Explicitly out of scope (restated from the task, binding)

No change to `can_native_update_3state`/`_2state`'s own threshold/local-field
FORMULA. No change to the already-shipped decay rules or the Hebbian
mechanism. No new Rust Term (all of `Log`, `Div`, `Plus`, `Minus`, `Max`,
`Min`, `IfThenElse`, `Gt`, `Lt`, `Eq`, `Not`, `And`, `Or`, `Attr`, `Lit`
already exist and are reused as-is — to be confirmed by `git diff --stat
main -- '*.rs'` being empty after the build, matching every prior rung in
this arc).
