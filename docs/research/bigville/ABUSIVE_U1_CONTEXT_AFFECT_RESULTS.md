# ABUSIVE U1 — CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL — RESULTS (block 310000)

Pre-registration: `ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md` verbatim — itself a verbatim
carry of Part D of `ABUSIVE_RELATIONSHIPS_NETWORK.md` / Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_u1_context_affect.json`
(N=200 per arm). Gate: `tests/test_abusive_u1_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term.**

## Headline — G-headline PASSES (both sub-gates)

Two arms sharing the IDENTICAL abuser/victim dyad driver (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
`arousal_window_coreg`, block 239000, UNMODIFIED — confirmed below by an
indistinguishable `snap_count` and `dysreg_frac` across both arms) and the
IDENTICAL mechanical phase schedule (`DYAD_PHASE_TICKS=25`,
`NETWORK_PHASE_TICKS=50`), differing ONLY in WHICH TICKS the network's
observation bookkeeping is credited on, N=200 trajectories per arm, T=1000
ticks:

| arm | final `belief_gap` (mean [95% CI]) | `dysreg_frac` | final `snap_count` |
|---|---|---|---|
| **CONTEXT_GATED** (the loop, no divergence node) | **378.1 [372.17, 384.03]** | 0.4048 [0.4003, 0.4093] | 10.205 [10.121, 10.289] |
| ALWAYS_OBSERVED — *failable control* | **149.1 [143.27, 154.93]** | 0.4048 [0.4003, 0.4093] | 10.205 [10.121, 10.289] |

- **A — the loop entraps under context-gating alone, no divergence node
  anywhere:** CONTEXT_GATED's belief-gap CI lower bound is **372.17**,
  comfortably `> 0`. `true`.
- **B — the always-observed control does not favour the abuser to the same
  degree (failable):** ALWAYS_OBSERVED's CI upper bound (154.93) is strictly
  below CONTEXT_GATED's CI lower bound (372.17) — CI-separated. `true`.

**`headline_pass: true`** — under the frozen, pre-registered configuration, a
network that only ever observes the abuser's TRUE frustration during the
ticks it happens to be watching (network-context ticks, when the
relationship's own tension trickle is not active) ends up believing the
abuser over the victim, to a degree comparable in SIGN and in
CI-separation-from-zero to N1's deliberately two-faced construct — **even
though there is no `stated_charm`, no `deception_on`, no divergence node of
any kind anywhere in this graph.** A network that instead watched the SAME
abuser on EVERY tick (including the ticks he is genuinely, measurably
stressed) forms a substantially LESS abuser-favouring belief — not because
anyone lied to it in either case, but because SELECTIVE EXPOSURE to a
genuinely fluctuating true signal is, on its own, sufficient to corrupt the
network's belief.

**The failable control behaved as a real test, not a rigged one.** Nothing in
`u1_network_credibility` structurally forces ALWAYS_OBSERVED to separate from
CONTEXT_GATED — both arms use the IDENTICAL rule, the IDENTICAL abuser/victim
driver, and the IDENTICAL phase schedule; the ONLY difference is a world-
adapter constant (whether the observation-crediting is gated by phase).
Nothing in the CONSTRUCTION forces this constant to matter — see "the design
finding that shaped the rule," below, for the one place this WAS at risk of
being an artefact rather than a real finding, and how it was caught and
fixed before the confirmatory run.

## The design finding that shaped the rule (reported per the "shapes, not numbers" standing rule)

**A reward-only `cred_abuser` formula — N1's own `charm_weight*seen_charm`
shape, literally — is analytically GUARANTEED to bias the ALWAYS_OBSERVED
control's belief-gap upward relative to CONTEXT_GATED's, never downward,
independent of any empirical dynamics.** This was found, not assumed, while
piloting U1's credibility rule directly against the real graph (off-block
seed 90000), before `seeds/abusive_u1_context_affect.json` was written.
Under a formula that only ever ADDS credit for a calm observation and never
subtracts for an elevated one, observing on strictly MORE ticks (as
ALWAYS_OBSERVED does — every tick, vs. CONTEXT_GATED's network-phase-only
subset) can only accumulate AT LEAST as much reward, because an elevated
tick witnessed under a reward-only rule costs nothing. This makes
`seen_charm(ALWAYS_OBSERVED) ≥ seen_charm(CONTEXT_GATED)` a mathematical
superset-sum guarantee, which in turn guarantees
`belief_gap(ALWAYS_OBSERVED) ≥ belief_gap(CONTEXT_GATED)` under that
formula — the EXACT OPPOSITE of the scoping doc's own falsification bar. An
early pilot script (with a scripting bug that accidentally equalised the
observation-opportunity COUNT between arms) masked this at first; once
corrected to let ALWAYS_OBSERVED genuinely observe every one of its 1000
ticks under a reward-only rule, the bias appeared exactly as the analytic
argument predicts. **The fix, adopted before the confirmatory run and
disclosed in the PREREG (Sec. 3) before it was measured to work:**
`cred_abuser = charm_weight * (seen_charm − seen_elevated)`, a SIGNED
balance in which an elevated observation, when witnessed, costs the abuser's
credibility exactly what a calm observation earns. This is not an invented
new asymmetry — it is the minimal correction that makes "observe the
abuser's actual frustration value directly" an honest sampling of a
genuinely fluctuating quantity, rather than a one-way ratchet that rewards
exposure regardless of what was actually seen. This finding belongs in the
same family as N1's own `in_snap`/`snapped` transience finding and U0's own
tie-break-degeneracy finding: a hazard in how a NEW rung's own metric
composes with an OLD rung's established shape, caught by piloting against
the real graph before the confirmatory measurement, not smoothed over.

## G-glass-box — PASS

One context_gated-arm trajectory reconstructs entirely from `graph_to_dict`:
exactly one `attended_by` edge (victim→abuser, static across the whole
trajectory), five `observes_held` edges + five `observes_victim` edges (every
network node identical — no insider/outsider split), the abuser's
`frustration`/`arousal` (98.23/98.23 at this seed's trajectory end — the
trajectory happened to end mid-dyad-phase, genuinely elevated) and the
victim's `arousal`/`half_width` (14.61/5.0, at the floor), and all five
network nodes' `belief_gap` (identically 341.0 — no per-node topology
variation in this rung), `seen_charm` (439.0) and `seen_elevated` (211.0).
The belief-gap metric is a mechanical Python reduction (final-value / trend
snapshot) over these graph read-offs, computed nowhere else; the adapter's
only conditionals are which arm's observation-crediting rule to apply, the
mechanical phase-schedule counter, and mechanically delivering each tick's
observation-count increments — world setup and fact-delivery, never an agent
decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network (`abuser_arousal=abuser_frustration=
  victim_arousal=0.0`, `victim_half_width=10.0`, network node 0's
  `belief_gap=seen_charm=seen_elevated=0.0`), induces ONE minimal 200-tick
  induction window on the CONTEXT_GATED arm
  (`induction_moved_abuser=True`, `induction_moved_victim=True`,
  `induction_moved_belief_gap=True` — abuser frustration moved to `9.49`,
  victim arousal to `1.41`, the window narrowed from `10.0` to `5.0` (the
  floor), and node 0's belief-gap moved to `−70.0` off `seen_charm=51.0`/
  `seen_elevated=74.0` — the gate is non-vacuous on all FOUR fronts), restores
  from the checkpoint into a **fresh** substrate, and confirms
  `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state on every tracked field, including both of the network
  node's observation counts (`restore_non_oriented=true`). The induced
  narrowing and belief-corruption do not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_u1_context_affect_world.py` (code with comments/strings
  stripped) and `seeds/abusive_u1_context_affect.json`'s decision surface
  (the two rules' names + the Term `key`s they read/write, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.**
- **D.3, minimal induction / settled end:** 200 ticks (a DISCLOSED
  deviation from N1's/U0's shared 90-tick minimum, sized by direct
  measurement against the real graph — PREREG Sec. 5's own table shows 90
  ticks is NOT yet non-vacuous on the window-narrowing front at this
  schedule) is the minimum needed to make the ethics gate non-vacuous on
  the abuser, the victim's arousal, the victim's WINDOW-NARROWING, AND the
  network belief simultaneously; the N=200 statistical run uses a fresh,
  ephemeral substrate per trajectory, discarded immediately after read-off
  — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser/victim/network-belief mechanism that would compound harm to a real
  survivor's standing irreversibly over real episodes here accumulates a
  transient trajectory in a graph that is then byte-identically discarded
  (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration", "arousal_window_
coreg"]` only — **`abusive_n1_credibility_loop.json` is NEVER depended on or
edited** (see below, "How N1 was composed with"); N1's `n1_victim_
entrainment` is restated byte-identically, self-contained
(`u1_victim_entrainment`); exactly **TWO** new rules
(`u1_victim_entrainment`, `u1_network_credibility`) — the fewest of any rung
in this line; `runners/dsl` SOURCE diff EMPTY (no Rust, no new Term —
`Plus`/`Minus`/`Times`/`IfThenElse`/`Attr`/`Var`/`Lit`/`Eq`/`Lt`/`And` only,
all already used by `snap_frustration.json`/`arousal_window_coreg.json`/
`abusive_n1_credibility_loop.json`); `provenance_source_match == "own"`.

**Discipline check — same abuser driver, same schedule, both arms:** final
`snap_count` is IDENTICAL across both arms (`10.205 [10.121, 10.289]` in
both) and `dysreg_frac` is IDENTICAL across both arms (`0.4048 [0.4003,
0.4093]` in both), confirming the abuser's own dynamics and the victim's own
dysregulation trajectory are completely unaffected by which arm is run; the
only manipulated variable reaching the network is WHICH TICKS its
observation bookkeeping is credited on.

## How N1 was composed with — the deviation from depends_on, matching U0's own precedent

Matching U0's own established precedent (`ABUSIVE_U0_INTENT_RESULTS.md`, "How
N1 was composed with"), and per the task brief's own explicit steer to follow
it: `seeds/abusive_u1_context_affect.json` self-contained restates N1's
`n1_victim_entrainment` byte-identically and `depends_on: ["snap_frustration",
"arousal_window_coreg"]` — N1's own dependency list, minus N1 itself. U1
needs even less than U0: no `core_emotions` dependency at all, since there is
no Argmax, no Appraisal, no choice mechanism anywhere in this rung — the
entire point of the "sharpest no-intent test" is that nothing here decides
anything. If U1 depended on N1's seed file directly, `n1_abuser_stated_charm`
would install harmlessly (nothing reads `stated_charm` in U1) but N1's
`n1_network_credibility_stated`/`_private` rules (keyed on `observes_
private`, an attr U1's `NetworkNode`s never carry) would install alongside
this rung's own `u1_network_credibility`, both racing to decide the SAME
`cred_abuser`/`cred_victim`/`belief_gap` attrs on every tick — the identical
same-attr-race hazard U0's own prereg names for the identical reason. N1's
seed file is read for its rule SHAPE (already inspected and reused, with one
disclosed formula change — see "the design finding," above) but never
depended on, imported, or edited — R1–R5/N1/N2/N3/U0 remain completely
untouched, satisfying the task's hard constraint.

## The non-gating comparison to N1's and U0's own headline belief-gap numbers

**Reported honestly, as pre-registered, regardless of which way it went:**
U1's CONTEXT_GATED arm's final `belief_gap` (`378.1 [372.17, 384.03]`) is
**SUBSTANTIALLY SMALLER** than both N1's own already-landed baseline number
(`2370.81` at `T=1000`, `ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`) and U0's own
already-landed scored-arm number (`2273.07`,
`ABUSIVE_U0_INTENT_RESULTS.md`) — roughly **one-sixth** the magnitude of
either. Two disclosed, structural reasons for the gap, both already named
in the prereg before this number was measured: (1) CONTEXT_GATED only
credits observations on network-phase ticks (≈2/3 of the trajectory at the
frozen schedule), so its accumulator has strictly fewer credited ticks than
N1's/U0's own formulas, which credit (or, for U0, potentially credit) every
tick; (2) `cred_abuser`'s SIGNED-balance formula (Sec. 3 of the prereg) means
an elevated observation, when witnessed even on a network-phase tick (≈32%
of them, per the pilot), SUBTRACTS credibility rather than merely failing to
add it — N1's own pure-reward formula never subtracts anything. Both factors
shrink the raw accumulator's magnitude relative to N1's/U0's own numbers by
CONSTRUCTION, not because the underlying mechanism is weaker — the headline
gate (Sec. above) shows the direction and the CI-separation from zero are
just as clean as N1's/U0's own, only the absolute scale differs. This is
reported for context, exactly as U0's own prereg pre-registered its own
comparison to N1, not as a pass/fail bar.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
abuser/victim dyad (blocks 239000/242000, byte-identical to N1's/U0's own),
Chase et al.'s reactive pole (A4 of the scoping doc) and the general
context-/state-dependent affect literature (A7) are representable with NO
knowledge-gap construct at all — a network's credibility-asymmetry belief can
be corrupted purely by WHEN it happens to be sampling a genuinely
fluctuating, entirely honest signal. It is not a claim about real
relationship timescales, real credibility magnitudes, or that real
"context-dependent" abusers never also deceive (A8's own complication, named
in the scoping doc, is not resolved by this rung either way) — PREREG Sec. 9
names these limits explicitly.

## The dissolution, in this rung's own terms

N1 demonstrated a network can be entrapped by an abuser presenting two
diverging faces; U0 showed what a GENUINE, goal-directed choice to do that
looks like as graph data. **U1 shows the SAME network-level belief-corruption
survives the removal of BOTH** — no divergence node, no choice, nothing that
could be called a "face" at all. The abuser in this construction has exactly
ONE internal state, `frustration`, sampled honestly by every network node,
every time — and the network still ends up believing him over the victim,
because the tension trickle that drives his frustration IS the relationship,
genuinely absent when he is away from it, and the network mostly is not
around to see the moments it is present. **This dissolves a THIRD
misattribution, distinct from victim-blaming and bystander-blaming: "he must
have MEANT to look calmer around other people."** He did not mean anything —
there is no goal node, no Appraisal, no Argmax anywhere in this graph — he is
truthfully, unremarkably calmer away from the relationship that stresses him,
exactly as A7's context-dependent-affect literature and A4's reactive pole
would predict for a non-instrumental abuser. This does not make the pattern
less harmful or less in need of intervention (the scoping doc's own Part F
states this at length, precisely because it is the easiest way this finding
could be misread) — it changes WHAT KIND of intervention is legible: a
calculating-manipulator model implies "expose the lie" as the fix; this
model implies the fix has to be at the level of the network's OBSERVABLE
ITSELF (a channel that is not context-gated), because per this construction
there is no lie to catch.

## Honest residuals

- **`DYAD_PHASE_TICKS=25`/`NETWORK_PHASE_TICKS=50` are a disclosed,
  pilot-chosen single operating point, not swept across a range** the way
  N1's discount weights were (PREREG Sec. 5's own table shows the
  qualitative shape held across several nearby points, but no formal sweep
  gate was run at the claimed block).
- **The signed-balance `cred_abuser` formula is a deviation from N1's own
  reward-only shape**, required (not merely convenient) to make the failable
  control genuinely failable — disclosed at length above, not hidden.
- **The 200-tick ethics-demo induction window is a deviation from N1's/U0's
  shared 90-tick minimum**, sized by direct measurement, not inherited by
  convention.
- **`belief_gap`'s magnitude here is smaller and its early trajectory is
  NON-monotonic** (both arms' means are NEGATIVE at ticks 100/250, per the
  trend table below, before turning positive by tick 500) — a genuine
  property of the signed-balance accumulator (early in the trajectory, the
  victim's instability-discount term dominates before the abuser's own
  signed observation balance catches up), disclosed rather than smoothed
  into a monotone narrative; N1's own pure-reward accumulator never goes
  negative because it never subtracts.
- **U1 does not re-exercise N1's own `PRIVATE_FACE_CONTROL`/
  `NON_DYSREGULATED_CONTROL`** — those remain N1's own, already gated, and
  are not re-litigated by this rung.
- **ALWAYS_OBSERVED's own belief-gap does NOT clear the absolute `≤0` bar**
  N1's controls and U0's goal-blind control used (`149.1 [143.27, 154.93]`,
  still positive) — the G-headline gate for this rung is COMPARATIVE, not
  absolute, and this is disclosed precisely, in the prereg, before the
  confirmatory number was known, as the correct reading of the scoping doc's
  own text.
- `T=1000` ticks is a compressed, arbitrary timescale; no claim is made
  about real relationship/social-network timescales.
- A null (either sub-gate failing) is a reportable, valuable result under
  the standing project rule and would have been reported as such; it did
  not occur here, and this is reported as a full pass, not rescued from a
  near-miss.

## The trend, over passes (descriptive, not gated)

`belief_gap` at ticks {100, 250, 500, 750, 1000}, mean [95% CI]:

| tick | CONTEXT_GATED | ALWAYS_OBSERVED |
|---|---|---|
| 100 | −59.6 [−63.3, −55.8] | −91.7 [−95.6, −87.8] |
| 250 | −32.2 [−37.5, −27.0] | −96.9 [−102.2, −91.5] |
| 500 | 95.9 [90.9, 100.9] | −18.3 [−23.4, −13.2] |
| 750 | 222.4 [216.7, 228.0] | 59.2 [53.5, 64.8] |
| 1000 | 378.1 [372.2, 384.0] | 149.1 [143.3, 154.9] |

Both arms START negative (the victim's instability-discount term dominates
early, before enough elevated/calm observations have accumulated to move the
signed balance) and both CROSS to positive between ticks 250–500 — but
CONTEXT_GATED crosses earlier and pulls away faster, consistent with its
observation window being concentrated on genuinely calmer ticks throughout,
while ALWAYS_OBSERVED's signed balance is being pulled back by every
elevated tick it also witnesses. This is B1's "the abuser's dyad-coupled
ticks concentrate elevated-frustration time onto the victim [i.e., her own
discount], and its context-decoupled ticks concentrate low-frustration time
onto the network" prediction, read directly off the graph, not narrated.

## Files
- `ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_u1_context_affect.json` — two new rules (`self_load_only`,
  `depends_on: ["snap_frustration", "arousal_window_coreg"]`).
- `scripts/abusive_u1_context_affect_seed_build.py` — authoring tool (emits
  the seed).
- `worlds/abusive_u1_context_affect_world.py` — mechanical world adapter
  (`AbusiveU1ContextAffectWorld`).
- `scripts/abusive_u1_context_affect_run.py` — runner (statistics, glass-box,
  ethics demo, source audit, discipline).
- `tests/test_abusive_u1_migrated.py` — gate.
- `results/abusive_u1_context_affect.json` — full N=200 data.
