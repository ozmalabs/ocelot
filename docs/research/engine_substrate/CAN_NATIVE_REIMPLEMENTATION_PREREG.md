# Native CAN reimplementation — items 1-3 as sd-loop/Γ-native mechanism — PREREG

Executes `CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md` (merged `main@325c064`,
verdict: **replace**, not hedged). This is a BUILD rung, not a spike.
Worktree `/home/matt/ozmadev/ocelot-worktrees/can-native-reimplementation`,
branch `can-native-reimplementation`, base `main @ e75142a` (re-verified via
`git log --oneline -1 main` before branching; `git worktree list`/`git branch
-a` showed no concurrent CAN work).

Per this session's own standing discipline (`CLAUDE.md` "SHAPES, NOT
NUMBERS" / "POWER THE GATE BEFORE THE ENDGAME"): every live-demonstration
scenario below is registered BEFORE the seed rules or test file exist. Two
open Term-composition questions the spike named as "very likely, not
confirmed" (§3.4/§8 point 4) were resolved by direct, live, throwaway probes
on the real engine BEFORE this document was written (not before the
predictions were registered) — reported honestly in §0 rather than smoothed
into "as predicted."

---

## 0. Two probes run before registering the design below, and what they found

The spike named one open question for item 3 ("pairing `EdgeAttr` with a
neighbour's `state` `Attr` inside one `Sum` ... was not traced to a worked
example") and left items 1-2's exact codebook encoding unspecified. Both were
checked live, on the real engine, via disposable scratch scripts (not
committed, not seeds) before this PREREG was written, because the answer
determines whether items 1-3 are buildable AT ALL under the "zero new Rust"
constraint — this is scoping work, not the registered experiment itself.

**Probe 1 (item 3's open question) — CONFIRMED, with one real, load-bearing
design consequence.** `Sum{source: Edges(Var("c"), "causal_influence"),
var_name: "e", value: Times([EdgeAttr(Var("e"),"weight"),
Attr(Nth(Var("e"),2), "state")])}` evaluates correctly — `Edges` returns
`(src, edge_type, tgt)` tuples, `Nth(e, 2)` extracts the target node,
`EdgeAttr`/`Attr` compose over it. **But `Edges` only returns OUT-edges**
(`shape_decode.rs`/`term.rs` confirmed: `out_edges_slice`) — there is no
existing Term that returns IN-edges as `(src,type,tgt)` tuples with attrs
attached (`InNeighbours` returns a bare node set, no edge attrs). This means
the native discrete-update rule reads coupling strength **asymmetrically —
only a Concept's own OUT-edges** — unlike `can_ops.rs::build_couplings`,
which explicitly walks both directions and symmetrizes
(`can_ops.rs:163-196`, confirmed by direct read in this pass, matching the
prior rung's own citation). **Design consequence, adopted here rather than
worked around with new Rust**: every network THIS rung builds for its own
live demonstrations populates `causal_influence` edges as **symmetric pairs**
(`A→B` and `B→A`, same weight) — a schema CONVENTION, not a Rust change, and
one that is honestly reported in §7's migration assessment as a REAL
difference from Bigville's existing single-direction schema (see §7).

**Probe 2 (items 1-2's codebook encoding) — CONFIRMED, and surfaced ONE
finding not anticipated by the spike, kept as a genuine (favorable) design
answer.** A held basin = a `ShapeSignature` node with `signature` = a list of
relation tuples `["state", <concept_name>, <sign>]`, one per concept. An
`Observation` node's `signature` in the same shape, decoded via
`ShapeDecode{goal, codebook_type:"ShapeSignature", wild_objects:false}`.
`field:"covered_by"` returns the single matching basin's name when the
observation matches EXACTLY one held configuration (residual empty, one-part
plan) — clean recognition. `field:"residual"` returns the uncovered relations
when NO held configuration explains the state at all. **The unanticipated
finding**: an observation that partially agrees with TWO conflicting basins
(e.g. two components matching one basin, one component matching the OTHER)
decodes with **residual EMPTY but `covered_by` = `None`** — the beam search
composes a multi-part plan drawing from BOTH basins
(`ordered_parts=('basin_anti','basin_pro')`, live-confirmed) to reach full
coverage. This is not a defect — it is a genuinely better frustration/
ambivalence signal than residual size alone: **`len(ordered_parts) > 1` on a
zero-residual decode is the decode-native reading of "torn between two
basins, needed material from both to explain," structurally closer to CAN's
own "multiple inconsistent views = multistable basins" than a scalar residual
count** — registered here as part of the design (§2), not discovered after
the fact.

Both probes are throwaway (not committed); their outputs are quoted verbatim
above as the basis for the design below, per this document's own register-
before-build discipline.

---

## 1. Item 3 — discrete-asynchronous evidence propagation, exact design

**Constant.** `ATANH_HALF = 0.5493061443340548` (`math.atanh(0.5)`,
Python-computed once at design time, hard-coded as a `Lit` — never computed
at runtime, no `Tanh` Term needed, matching the spike's own §3.4 sizing).

**Local field term** (reused per rule, same shape as Probe 1):
```
local(c) = Attr(c,"external_field") + Attr(c,"identity_field")
           + Sum_{e in Edges(c,"causal_influence")} EdgeAttr(e,"weight") * Attr(Nth(e,2),"state")
scaled(c) = local(c) * Attr(mt,"temperature")
```
This is the exact discrete-update twin of `can_ops.rs::mt_mean_field_marginal`'s
`local = h + Σ J·σ_j` (`can_ops.rs:256-264`), MINUS the `tanh`/damping
relaxation — the discrete rule decides a **committed jump**, not a blended
step.

**Three-state rules (native CAN vocabulary, "σ ∈ {-1,0,+1}", the DEFAULT
mechanism)**, each `match_type:"Concept"`, `match:[["mt","has_concept","c"]]`,
guarded additionally by `Eq(Attr(mt,"discrete_mode"),Lit("3state"))`:

- `can_native_update_plus`: `where = scaled > ATANH_HALF AND state != 1`;
  `effects = set_attr(c,"state",1)`.
- `can_native_update_minus`: `where = scaled < -ATANH_HALF AND state != -1`;
  `effects = set_attr(c,"state",-1)`.
- `can_native_update_zero`: `where = -ATANH_HALF <= scaled <= ATANH_HALF AND
  state != 0`; `effects = set_attr(c,"state",0)`.

**Two-state rules** (classical Hopfield, no deadzone — built for the
convergence-guarantee COMPARISON only, guarded by
`Eq(Attr(mt,"discrete_mode"),Lit("2state"))`):

- `can_native_update_plus_2state`: `where = local >= 0 AND state != 1`.
- `can_native_update_minus_2state`: `where = local < 0 AND state != -1`.

**Why this is genuinely asynchronous with zero new Rust — confirmed by
reading `rewrite.rs::run_rules_opts`, not assumed**: the non-batch ("cold
path") loop collects ALL bindings for rule *i*, applies exactly ONE
progressing binding, commits it, then moves to rule *i+1* — which
re-matches against the JUST-UPDATED graph (`rewrite.rs:2183-2199`). Across
one `while` pass, later rules (and the SAME rule on its next pass) see
earlier commits. This is Gauss-Seidel/asynchronous update BY THE ENGINE'S
OWN DEFAULT EXECUTION MODEL — not a property this rung has to build. Probe 1
(§0) already demonstrated this live on a 2-concept toy network with the
hand-derived expectation matching exactly.

**Registered predictions (item 3 live demo, `test_can_native_reimplementation.py`)**:
mirror `can_concept_poc_discrete_async.py`'s own design exactly, on the REAL
engine instead of pure Python: N=8 complete graph, `pair_rng`/`field_rng`
seeded per-draw, coarse (3-level `J`) vs fine (9-level `J`) vocab, β=2.0,
N_DRAWS=20 per condition (smaller than the PoC's 30 — real PyO3 graph
construction per draw is far more expensive than pure-Python dict math; sized
for this rung's own time budget, named honestly as a smaller sample, not
silently matched to 30).

1. Continuous-sync (via the EXISTING `mt_relax_to_marginal`/
   `mt_mean_field_marginal` PyO3 surface, `damping=1.0` — reproducing the
   OLD pre-fix update exactly, per `CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md`
   §1's own cross-check) oscillates on at least one draw (replicates the
   already-measured pathology on THIS rung's own real-engine draws, not
   merely cited).
2. Discrete-async 2-state (native rules, real `run_rules` fixpoint):
   0/20 non-convergent in both conditions (`run_rules` returns steps <
   max_steps on every draw — a genuine fixpoint, no rule progressed on the
   final pass).
3. Discrete-async 3-state: predicted small but not guaranteed by the same
   proof (per the spike's own §5.1 deadzone gap) — reported honestly
   whichever way it comes out, exactly as the PoC did.
4. Bonus, not the primary claim: whether 3-state converges to lower or
   higher frustration than 2-state (the PoC found HIGHER for 3-state,
   contrary to its own first guess — checked again here, reported precisely,
   not assumed to replicate).

---

## 2. Items 1-2 — basin classification + residual-as-coherence, exact design

**Codebook.** `ShapeSignature` nodes, `name` + `signature` = relation tuples
`["state", <concept_name>, <sign>]` for every concept in the network's
5-topic (Bigville) or N=8 (item-3-network) template. Held configurations are
REAL convergent states from the item-3 discrete-async relaxation (not
hand-picked round numbers) — a basin the mechanism itself settles into,
decoded against a codebook seeded from OTHER real settled states, avoiding
a circular "decode against itself" demonstration.

**Decode.** `Observation{signature: <live concept states, quantized to
{-1,0,+1}>}`, `ShapeDecode{codebook_type:"ShapeSignature", wild_objects:false}`.

**Classification (item 1)**: `field:"covered_by"` — the single matching
basin's `name`, or `None` if no single configuration explains the state.

**Coherence/frustration (item 2)**: reads BOTH signals Probe 2 surfaced,
not residual alone:
  - `field:"residual"` (count) — relations no held configuration explains at
    all (genuine novelty / undifferentiated commitment, the "state near 0"
    reading).
  - `field:""` (full dict) → `len(ordered_parts)` — how many DISTINCT held
    basins had to be drawn on to explain the state (>1 = torn between
    basins, the frustration/ambivalence reading).
  - `coherent` ⟺ `residual == () AND len(ordered_parts) == 1`.

**Registered predictions (live demo)**: (a) a state EXACTLY matching one held
basin decodes `covered_by = <that basin's name>`, `residual = ()`,
`ordered_parts` length 1 — clean recognition; (b) a state genuinely torn
between two held basins (built by hand-mixing components from two draws, half
from each) decodes with `covered_by = None` and EITHER nonzero residual OR
`ordered_parts` length > 1 — a visibly distinguishable frustrated/ambiguous
read against (a)'s clean one; (c) an all-zero (uncommitted) state decodes
with the LARGEST residual of the three cases tested — consistent with the
already-wired `curiosity_targets_ambivalent_nodes` rule's own "near-zero =
ambivalent" reading.

---

## 3. Item 4 — mint-on-recurrence for edge CREATION only

**Checked before designing**: `grep -rn "logodds" runners/dsl/src/*.rs
seeds/*.json` finds it named ONLY in `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`
and `CAN_BELIEF_QUANTIZATION_PREREG.md` — **confirmed still unbuilt**, exactly
as the spike found. Per the task's explicit scope: build ONLY mint-on-
recurrence for edge creation; name graded reweighting as blocked on the
still-unbuilt `logodds` generator (not attempted); name decay as having no
proposed native analog (not attempted, per the spike's own honest gap).

**Design**: two Concepts `a`,`b` under the same Mt, no existing
`causal_influence` edge between them (checked via `Not(Exists(...))` over
`Edges(a,"causal_influence")`/`Edges(b,"causal_influence")`), both committed
to the SAME sign (`state(a) == state(b)` and both `!= 0`) for
`co_occur_count >= 2` (recurrence, not first occurrence — the sd loop's own
recognize-vs-mint threshold shape) — increments `co_occur_count` on the pair
each tick they co-activate (a small counter-attr on the Mt, keyed by pair,
OR simpler: on a dedicated `Coactivation` edge/node between the two
Concepts) and mints a `causal_influence` edge (weight = sign, i.e. +1 for
same-sign co-activation) once the threshold is crossed. Registered
prediction: a real, live pair that co-activates across 2+ ticks with no
prior edge mints EXACTLY ONE `causal_influence` edge; a repeat co-activation
after minting does NOT re-mint (recognized, not re-created) — the same
"shown not to re-mint on repeat" gate blob-edge minting uses.

---

## 4. Item 5 — polarization re-test via `max_steps`/`beam`, attempt-if-cheap

Per the spike's own naming (§7 point 5): re-run `can_concept_poc_decode_
polarization.py`'s design on the REAL `ShapeDecode` Term, sweeping `max_steps`
(refinement depth) instead of a symmetric vote-count `scrutiny_T`, to check
whether THIS parameter sharpens monotonically where `scrutiny_T` did not
(the PoC's own honest U-shape correction). Registered prediction: as
`max_steps` rises, `frac_resolved_near_extreme` should NOT be U-shaped the
way `scrutiny_T` was (since `max_steps` is not symmetric under
complementation the way a vote threshold is) — reported honestly whichever
way it comes out. Attempted only if it fits this rung's time budget after
items 1-3; if not, named precisely as not attempted (matching the spike's
own §5.4 closing line — "the natural next test this section names but does
not run").

---

## 5. Migration-decision assessment plan (Bigville)

`worlds/bigville_can_beliefs.py::build_resident_can_mt`'s `STRUCTURAL_EDGES`
loop (`:176-181`) mints **ONE direction per structural pair** (`s.add_edge(
concepts[a], "causal_influence", concepts[b], ...)`). §0/Probe 1 above
already establishes the native discrete rule's `Sum` reads OUT-edges only.
**Registered check, not yet run**: build ONE resident's real CAN network via
the EXISTING `build_resident_can_mt` unmodified, run the native discrete
rule set on it, and directly compare the resulting local fields / converged
states against `mt_mean_field_marginal`'s (symmetric-coupling) values on the
SAME network — if they diverge (predicted: yes, because Bigville's schema is
asymmetric and the native rule does not symmetrize), that is the concrete,
measured basis for the migration recommendation (either Bigville's builder
needs a one-line change to mint symmetric pairs, or the native rule needs
new Rust it does not currently need) — reported in RESULTS, not assumed.

---

## 6. What this PREREG does not cover

Async/Gauss-Seidel RANDOMIZED scheduling (the sibling damping-fix rung's own
named-not-built item) — the native rule's determinism is a DIFFERENT, engine-
default-order asynchrony, not addressed here. Basin ENUMERATION (search over
all basins a network could hold) — per the spike's own §3.1/§6 point 2, out
of scope, not needed by anything this project has built. Sparse/non-complete
topologies beyond what item 3's N=8 complete-graph demo tests.
