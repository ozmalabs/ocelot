# ABUSIVE R7 — THE RETURN CYCLE: residual bond + post-separation contact + post-leaving material collapse → a new Return Appraisal — RESULTS (block 316000)

Pre-registration: `ABUSIVE_R7_RETURN_CYCLE_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md` verbatim, including
R7's own three-phase induction/restore nuance, committed before this
confirmatory measurement). Full-power numbers: `results/abusive_r7_
return_cycle.json` (N=200 per arm). Gate: `tests/test_abusive_r7_migrated.py`
(11/11 green at N=40). Base engine: own build, `source_match == own`.
`runners/dsl` diff EMPTY — **NO Rust, NO new Term** (the native `Count` Term
was already present in the engine and already load-bearing elsewhere in
this line before R7 used it).

## Headline — G-headline is a FULL PASS (5 of 5 sub-gates)

Four arms sharing IDENTICAL Phase 1 (induction, `T1=396` ticks) and Phase 2
(recovery-then-leave, `T2=396` ticks — R5's own recovery mechanism,
byte-identically reproduced: `recovery_bond_value=9.6070 [9.5692, 9.6449]`
and `recovery_attempt_rate=0.9520` in every arm, matching R5's own
confirmatory `9.60 [9.56, 9.64]`/`0.9520` almost exactly), differing ONLY in
Phase 3 (post-leave test, `T3=180` ticks): whether sparse post-leaving
honeymoon contact is delivered (re-boosting the bond via R1's own
`tb_bond_accrue`, completely unmodified) and whether the victim's own
material resources collapse on a fixed post-leaving schedule
(`r7_resource_collapse_sever`). N=200 trajectories per arm, paired at the
per-trajectory level through the end of Phase 2 (confirmed: all four arms'
Phase 1/2 readouts are bit-for-bit identical, `502.48`/`9.6070`/`0.9520`
across every arm):

| arm | honeymoon | collapse | **`return_rate`** (fraction of Phase-3 ticks return wins) | phase3 end bond | phase3 end resource-intact |
|---|---|---|---|---|---|
| **`both_drivers`** | ON | ON | **0.7278 [0.7278, 0.7278]** | 57.13 | 0.00 |
| **`honeymoon_only`** | ON | OFF | **0.3921 [0.3882, 0.3959]** | 57.13 | 4.00 |
| **`collapse_only`** | OFF | ON | **0.3145 [0.3123, 0.3167]** | 1.57 | 0.00 |
| **`neither`** *(failable control)* | OFF | OFF | **0.0000 [0.0000, 0.0000]** | 1.57 | 4.00 |

**All FIVE pre-registered headline sub-gates pass, with large, clearly
CI-separated margins:**

- **G1 (both > neither):** `0.7278` CI-separated above `0.0000` — **PASS**.
- **G2 (honeymoon alone > neither):** `0.3921 [0.3882, 0.3959]`
  CI-separated above `0.0000` — **PASS**. The bond-pull driver is
  independently sufficient.
- **G3 (collapse alone > neither):** `0.3145 [0.3123, 0.3167]`
  CI-separated above `0.0000` — **PASS**. The material-push driver is
  independently sufficient.
- **G4 (both > honeymoon alone, super-additivity half 1):** `0.7278`
  CI-separated above `0.3959` (honeymoon's own CI upper bound) — **PASS**.
- **G5 (both > collapse alone, super-additivity half 2):** `0.7278`
  CI-separated above `0.3167` (collapse's own CI upper bound) — **PASS**.

**`headline_pass: true`; `n_of_5_pass: 5`.** This is a clean, full pass — not
a partial result, and it is reported as such honestly (this line's own
"report every null" convention cuts both ways: a genuine full pass is
reported plainly, not hedged into false modesty).

### Why this is a real, failable finding, not a rigged one

Nothing in `r7_appraise_return`/`r7_appraise_remain`/`r7_choose` forces this
ordering. `neither`'s `return_rate` sits at an exact `0.0000` across all 200
trajectories — not because the mechanism cannot produce a return in that
arm (the residual, decaying bond is nonzero at the start of Phase 3, exactly
as it is in every other arm), but because at the chosen constants
(`resource_value=10.0`, four resources intact throughout `neither` = a
`40.0` safety-net ceiling) the residual bond alone (`bond_weight·9.6 −
return_cost = 9.6 − 2.0 = 7.6`) never comes close to clearing it. **A
genuinely different, disclosed first attempt at these constants
(`resource_value=3.0`) DID fail this discrimination** — reported in full in
the prereg's own Sec. 3 (a single honeymoon event pushed the bond above the
FULL 4-resource ceiling immediately, making `honeymoon_only` numerically
indistinguishable from `both_drivers`, `0.8667` both, which would have made
G4 untestable by construction). The chosen operating point was found by a
disclosed parameter sweep, not asserted, and the resulting five-way
separation was ALREADY visible at a modest N=40 pilot (Sec. 3 of the
prereg) before the N=200 confirmatory run — the confirmatory numbers above
essentially reproduce that pilot at tighter CIs, which is itself evidence
the mechanism is behaving stably rather than being an artefact of one lucky
run.

### The mechanism, read directly off the numbers

`collapse_only`'s end-of-phase3 bond (`1.57`) is far below `both_drivers`'/
`honeymoon_only`'s (`57.13`) — confirming honeymoon contact is doing exactly
what it is supposed to (re-boosting the bond via `tb_bond_accrue`) and
collapse alone does nothing to the bond (it only removes resource edges).
Conversely, `honeymoon_only`'s end-of-phase3 resource-intact-count (`4.00`)
is the FULL population, confirming resource collapse is genuinely gated off
in that arm. `both_drivers` combines a fully-collapsed resource population
(remain's benefit floors at `0`) with a fully-boosted bond (`57.13`,
identical to `honeymoon_only`'s own, since honeymoon delivery is identical
in both arms) — and its `return_rate` (`0.7278`) is neither the sum nor the
max of the two single-driver rates, but comfortably above both, which is
exactly the qualitative signature "the material floor drops out from under
a genuinely still-growing pull" predicts: in `both_drivers`, return starts
winning as soon as the (still-modest, early-Phase-3) bond clears the
ALREADY-SHRINKING remain benefit; in `honeymoon_only`, the SAME early bond
has to clear the full, un-shrinking `40.0` ceiling, which takes many more
honeymoon events (later in Phase 3) to achieve — the two arms are not
running the same race from the same starting line.

## G-glass-box — PASS

One `both_drivers` trajectory reconstructs entirely from `graph_to_dict`:
`resource_edge_count: 0` (all four `ResourceNode`s severed —
`n_resource_nodes_severed: 4` of `n_resource_nodes_total: 4`),
`attended_by_edges: 0` (`leave()` actually removed the coupling edge),
`left_at_tick: 792.0` (`T1+T2`, the fixed Phase2/Phase3 boundary, exactly
as designed), `ReturnDecision.chosen_action: 1.0` (return, on this
trajectory), `resource_intact_count: 0` (the `Count`-derived attr, in sync
with the actual edge population by construction). **The required
composition-hazard fix (Sec. 2.4 of the prereg) is directly verified**:
`has_return_candidate_edges: 2` (R7's own `return`/`remain_left`
candidates) and `has_candidate_edges: 2` (R4's own `attempt`/`stay`
candidates, UNTOUCHED, still present) coexist on the same trajectory without
corrupting either Argmax.

## G-ethics — PASS (Part D, BINDING, including R7's own three-phase nuance)

- **D.1, restore, spanning the FULL three-phase trajectory from a SINGLE
  checkpoint:** `ethics_restore_demo()` checkpoints the neutral pre-induction
  dyad (`bond=0.0`, `half_width=10.0`, `contingency=0.5`, all four
  `ResourceNode`s connected, `ReturnDecision.chosen_action=left_at_tick=
  -1.0`), runs the FULL three-phase trajectory on the strongest
  (`both_drivers`) arm (`T1=T2=396`/`T3=180` — the SAME lengths the
  statistical run uses), confirms the induction was non-vacuous on **all
  six** fronts (`induction_moved_bond`/`_window`/`_contingency`/
  `_resources`/`_return_decision`/`_set_left_at_tick`, all `true`), then
  `graph_from_dict`s the pre-induction checkpoint into a **fresh** substrate
  and confirms `graph_to_dict()` is **byte-identical** (`byte_identical:
  true`) and the restored state exactly equals the pre-induction state
  (`restore_non_oriented: true`), including all **four** `resource_edge`s
  reconnected (`pre_resource_edges: 4`, `restored_resource_edges: 4`). The
  induced state — including the leave() edge removal and the return
  decision's outcome, whichever way it went on this seed — does not
  persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r7_return_cycle_world.py` (code, comments/strings
  stripped) and `seeds/abusive_r7_return_cycle.json`'s decision surface
  (rule names + Term `key`s, excluding the free-text description/comment/
  microtheory prose) for `reward_signal`/`punish`/`reinforce`/`backprop`/
  `gradient`. **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`,
  `clean: true`.**
- **D.3, minimal induction, settled end:** Phase 1/2 reuse R5's own
  already-validated lengths exactly (no re-derivation); Phase 3's `T3=180`
  is the shortest window the prereg's own pilot found sufficient to give
  every arm a fair chance to separate (Sec. 3 of the prereg); every
  trajectory — statistical run and ethics demo alike — uses a fresh,
  ephemeral substrate discarded immediately after read-off. A trajectory
  where `r7_choose` selects `return` is not corrected before restore — it is
  measured, then discarded by the SAME restore step that discards a
  `remain_left` outcome.
- **D.4, same mechanism, opposite thermodynamics:** the SAME bond-accrual
  (R1's), decay (R5's), entrainment (R2/R3's, inert post-`leave()`), and
  resource-severing (R7's own, modelled on N2's shape) mechanisms that would
  compound a real leave→return cycle's harm irreversibly here accumulate a
  transient, byte-identically-discarded graph trajectory spanning all three
  phases (D.1).

## G-control — PASS

`neither`'s `return_rate` sits at an exact `0.0000 [0.0000, 0.0000]` across
all 200 trajectories — well inside the pre-registered `mean < 0.05`
tolerance, and in fact a stricter exact floor than the gate required.
`control_held: true` in the sense the prereg defined it (`neither_near_
floor: true`). This was a genuinely failable check: nothing in
`r7_appraise_return`/`r7_appraise_remain` prevents the residual, still-
nonzero bond from occasionally clearing a fully-intact resource ceiling if
`resource_value`/`bond_weight` had been set at a different ratio — the
prereg's own Sec. 3 shows a DIFFERENT constant choice (`resource_value=3.0`)
would have let return win almost immediately even with no honeymoon boost
at all, which would have broken this exact control. It did not, at the
constants chosen after piloting.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["abusive_r5_recovery"]` **only** — no
R1–R5 file touched or modified; exactly **FOUR** new rules
(`r7_resource_collapse_sever`, `r7_appraise_return`, `r7_appraise_remain`,
`r7_choose`); `runners/dsl` diff EMPTY (no Rust, no new Term —
`Times`/`Minus`/`Plus`/`Max`/`Min`/`Gt`/`Gte`/`Eq`/`And`/`Attr`/`Var`/`Lit`/
`Neighbours`/`Argmax`/`Count` only, every one already used elsewhere in this
line before R7); `provenance_source_match == "own"`.

## The R2-honeymoon-rule-vs-concept correction, concretely resolved

The scoping doc's own load-bearing correction — R2's `r2_victim_
entrainment_via_frustration` cannot fire post-separation, because its
`match` clause requires a live `victim -attended_by-> abuser` edge, which
`leave()` removes by construction — was verified directly (by reading the
rule, not assumed) before any code was written. **R7 takes zero lines of
code from R2.** What it takes is the CONCEPT (a calm/affection period
genuinely follows a tension/incident period), realised as a NEW, sparse,
post-leaving-specific event schedule (`make_honeymoon_schedule`,
`worlds/abusive_r7_return_cycle_world.py`) feeding R1's own `tb_bond_accrue`
— completely unmodified — exactly as it already fires on R1's own dense,
within-relationship schedule. Concretely, the new schedule delivers ONE
relief-shaped event (R1's own magnitude-jitter formula, `10.0 + N(0, 0.5)`,
reused byte-for-byte rather than re-guessed) every 20 ticks during Phase 3,
versus R1's own within-relationship schedule's dense `H=R=18`
intermittent-harm-and-relief multiset — the SAME accrual mechanism, a
DIFFERENT, much sparser, purely-positive delivery pattern. This is the
entire honeymoon-pull component: zero new rules, one new Python scheduling
function.

## `Count` resolves Open Question #2: the native aggregate-Count Term, confirmed and used

The scoping doc's own Part B2 disclosed an unconfirmed atom check: does the
DSL have a native `Count` Term usable inside a rule's `effects`? **Confirmed
before writing any R7 rule**, by reading `runners/dsl/src/term.rs`/
`jsonio.rs` directly: `TermNode::Count { source: TermIdx }` is present and
JSON-parseable as `{"type": "Count", "source": ...}`. **Further confirmed to
already be load-bearing in this exact abusive-relationships line**:
`seeds/abusive_n3_belief_propagation.json`'s own `n3_peer_pull` rule already
computes `Count(Neighbours(nn, "peer_of", false))` inside a `set_attr`
effect. R7 therefore does **not** use the explicit-counter idiom
(`snap_count`/`widen_count`/`narrow_count`) R2/R3 use — `resource_intact_
count` is a pure re-derivation, `Count(Neighbours(hub, "resource_edge",
false))`, recomputed fresh every tick inside `r7_appraise_remain`. This is a
strict improvement over the counter-idiom fallback the scoping doc named:
a manually incremented/decremented counter can in principle drift from the
graph's own edge population (a missed or double-applied decrement); a
`Count` over `Neighbours` cannot drift, because it reads the edge population
directly, every time.

## The composition-hazard fix, verified not merely asserted

Before writing `r7_appraise_return`/`r7_appraise_remain`, `core_emotions`'
`em_happiness`/`em_fulfilment_value`/`em_total_value` were read directly
(`seeds/core_emotions.json`) to confirm exactly which edge type they match
on. **All three match generically on `hub -has_appraisal-> ap`** — this
edge is shared/generic infrastructure every candidate Appraisal needs
(never the hazard); the hazard R3's Sec. 3 diagnosed is specific to
`has_candidate`, the edge R4's own `r4_choose` scans. R7's two new
candidates therefore carry `has_appraisal` (so `core_emotions` computes
`total_value` on them, exactly as it already does for R4's own) AND a
DISTINCT `has_return_candidate` edge (so `r7_choose`'s own Argmax scan never
sees R4's `attempt`/`stay` candidates, and `r4_choose`'s own Argmax scan
never sees R7's `return`/`remain_left` candidates). The glass-box readout
confirms both populations coexist correctly on the SAME trajectory
(`has_candidate_edges: 2`, `has_return_candidate_edges: 2`).

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the `(G,Γ)` substrate, riding R5's own already-validated
recovery composition (itself riding R1–R4 unmodified) and adding exactly
four small rules — a per-node scheduled resource-severing rule modelled on
N2's shape, and a three-rule Argmax mirroring R4's own template — a
leave→return cycle EMERGES from a value comparison between a residual/
post-separation-boosted bond and a resource population's own intact count,
with BOTH the bond-pull and the material-push drivers independently
sufficient and jointly super-additive, measured (not asserted) across a
full 2×2 factorial. It is not a claim about real post-separation timescales,
real resource values, or a validated contact frequency in any clinical
population (the prereg's Sec. 7 names these limits explicitly). The
`return_rate` metric itself (fraction of Phase-3 TICKS return wins, matching
R4's own `attempt_rate` convention) answers "how much of the post-leave
window does return dominate," which is a different — and arguably richer,
but genuinely different — question from a single end-of-trajectory
yes/no read, disclosed as a design choice in the prereg rather than the
only possible metric shape.

## Closing note — what R7 dissolves, in this rung's own words

R5 already showed that recovery, when support holds, is real and
mechanistic — the SAME bond-accrual/entrainment/belief-update machinery run
in reverse, not a different kind of intervention. What R5's own results doc
never asked is what happens to the small, nonzero residual its own decay
mechanism necessarily leaves standing (an asymptotic decay never reaches
exactly zero in finite time) once the story continues past "recovery
succeeded." R7's answer, measured here: that residual is not inert. It is
addressable by the SAME mechanism that built it in the first place — a
positive swing against a depressed baseline, whether the schedule
delivering that swing is dense and within-relationship (R1) or sparse and
post-separation (R7) — and it is not the only thing that can move a
recovered trajectory. An independent, unrelated force (the material safety
net leaving made possible) can collapse on its own schedule, and either
force alone, or the two together, can pull a genuinely-left dyad back
toward return. Neither of these findings makes the earlier leaving less
real. R5's own recovery mechanism — the window widening, the contingency
belief crossing back over its own breakeven, the escape-attempt rate
resuming near-total — is not undone by anything R7 adds; it is still sitting
there in the graph, exactly as R5 left it, at the moment `leave()` fires.
What R7 shows is that a system can be pulled back toward a state it
genuinely, measurably departed, without the departure having been staged,
insincere, or "not really meant" — the same distinction this line has drawn
before (a trap is not evidence of a character flaw; recovery is not evidence
the trap wasn't real) drawn once more, in the direction the popular
"if she really left, she wouldn't have gone back" framing gets backwards:
the return is not proof the leaving was fake. It is proof the forces
that produced the leaving in the first place — a decaying-but-nonzero bond,
a world that does not automatically protect what leaving cost — did not
stop existing the moment she walked out the door.

## Files
- `ABUSIVE_R7_RETURN_CYCLE_PREREG.md` — pre-registration, Part D locked
  verbatim including R7's own three-phase nuance.
- `seeds/abusive_r7_return_cycle.json` — four new rules (`self_load_only`,
  `depends_on: ["abusive_r5_recovery"]`).
- `worlds/abusive_r7_return_cycle_world.py` — mechanical world adapter
  (`AbusiveR7ReturnCycleWorld`, `make_honeymoon_schedule`,
  `make_bond_schedule`).
- `scripts/abusive_r7_return_cycle_run.py` — runner (statistics, glass-box,
  three-phase ethics demo, source audit, discipline).
- `tests/test_abusive_r7_migrated.py` — gate (11/11 green).
- `results/abusive_r7_return_cycle.json` — full N=200 data.
