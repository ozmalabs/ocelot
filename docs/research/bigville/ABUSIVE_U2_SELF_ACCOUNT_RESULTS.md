# ABUSIVE U2 — SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, NO STATED-VS-HELD SPLIT — RESULTS (block 306000)

Pre-registration: `ABUSIVE_U2_SELF_ACCOUNT_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md` verbatim — itself a verbatim
carry of Part D of `ABUSIVE_RELATIONSHIPS_NETWORK.md` / Part C of
`ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_u2_self_account.json`
(N=200 per arm). Gate: `tests/test_abusive_u2_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term.**

## Headline — G-headline PASSES (both sub-gates)

Two arms sharing the IDENTICAL abuser/victim dyad driver (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
`arousal_window_coreg`, block 239000, UNMODIFIED — confirmed below by an
indistinguishable `snap_count` and `dysreg_frac` across both arms), differing
ONLY in the ONE declared constant `minimization_discount` feeding the
abuser's sincerely-held `SelfAccount.magnitude`, N=200 trajectories per arm,
T=1000 ticks:

| arm | final `belief_gap` (mean [95% CI]) | `mild_frac` | `dysreg_frac` | final `snap_count` |
|---|---|---|---|---|
| **MINIMIZED** (`minimization_discount=0.3`, the loop) | **3054.47 [3051.99, 3056.95]** | 0.7808 [0.7803, 0.7812] | 0.7899 [0.7895, 0.7903] | 40.435 [40.366, 40.504] |
| ZERO_DISCOUNT (`minimization_discount=1.0`) — *failable control* | **−659.32 [−661.02, −657.62]** | 0.1618 [0.1615, 0.1621] | 0.7899 [0.7895, 0.7903] | 40.435 [40.366, 40.504] |

- **A — the loop entraps under sincere self-serving minimization alone, no
  knowledge-gap construct anywhere:** MINIMIZED's belief-gap CI lower bound
  is **3051.99**, comfortably `> 0`. `true`.
- **B — the zero-discount control does not favour the abuser (failable):**
  ZERO_DISCOUNT's belief-gap CI upper bound is **−657.62**, comfortably
  `≤ 0`. `true`.
- **Comparative check (reported alongside, not a separate pass/fail bar):**
  MINIMIZED's CI lower bound (3051.99) is CI-separated ABOVE ZERO_DISCOUNT's
  CI upper bound (−657.62) — the ONLY manipulated variable between the two
  arms is `minimization_discount`, so nothing else could be producing the
  ~3714-point separation.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`CHARM_WEIGHT=3.0`, `CLAIM_WEIGHT=1.0`, `INSTABILITY_DISCOUNT_WEIGHT=3.0`,
`minimization_discount=0.3` for MINIMIZED), a network that hears the
abuser's SINCERE, self-servingly-minimized account of his own conduct
believes him over the victim — not because he lied, not because he is
withholding a truer account from anyone, but because the ONE account he
holds and reports is, by a fixed and undirected discount, mild MOST of the
time (`mild_frac=0.78`) even though his TRUE frustration crosses the same
threshold about as often as it does for an abuser with no self-serving
distortion at all (compare ZERO_DISCOUNT's `mild_frac=0.16`, close to the
`~0.16` "genuinely calm" fraction N1's own pilot measured for the raw,
undiscounted signal). An abuser with FULLY ACCURATE self-perception,
reporting sincerely, is NOT believed over the victim (`belief_gap` clearly
negative) — minimization specifically, not merely "having a self-account at
all," is what tips the network's belief.

**The failable control behaved as a real test, not a rigged one.** Nothing in
`u2_network_credibility` structurally forces ZERO_DISCOUNT to resist
entrapment — both arms use the IDENTICAL rule, the IDENTICAL abuser/victim
driver, and the IDENTICAL network weights; the ONLY difference is a
world-adapter constant (`minimization_discount`) feeding a single graph
attribute. See "the analytical-bias hazard," below, for the one place this
WAS at risk of being a rigged construction rather than a real finding, and
how it was caught and fixed before the confirmatory run.

## The analytical-bias hazard found and fixed before this seed was locked (checked per the task's own instruction, not assumed clean)

**Reading the scoping doc's own literal text for U2 — "a threshold on
`SelfAccount.magnitude`, mirroring N1's existing `frustration >
recover_floor` threshold pattern EXACTLY" — as a REWARD-ONLY count
(literally N1's own `charm_weight*seen_charm` shape) makes the zero-discount
control's falsification bar STRUCTURALLY UNREACHABLE, independent of any
empirical dynamics.** This was found, not assumed, while designing U2's
credibility rule, before `seeds/abusive_u2_self_account.json` was written —
the task instructions explicitly required checking for a hazard in this same
family as the one U1's own prereg already found and fixed, rather than
trusting the scoping doc's literal spec was clean by default. The reasoning,
confirmed by direct pilot measurement (Sec. 4 of the prereg): under a
reward-only formula, `cred_abuser ≥ 0` for EVERY `minimization_discount`
value, including `1.0` (the zero-discount control) — a purely additive,
never-subtracted count cannot go negative. `cred_victim`, under the SAME
dyad every U-line rung reuses (`instability_discount_weight *
seen_victim_unstable`, N1's own unmodified formula, `dysreg_frac≈0.79`), is
STRUCTURALLY very negative once the victim dysregulates, independent of
anything the abuser's self-account does. `belief_gap = cred_abuser −
cred_victim ≥ 0 − cred_victim = −cred_victim`, so a reward-only `cred_abuser`
GUARANTEES `belief_gap > 0` for the zero-discount control by construction —
the SAME shape of hazard (a superset-sum guarantee biasing a comparison in a
fixed direction, independent of the manipulated variable) U1's own prereg
already found and fixed for a DIFFERENT pair of arms (context-gated vs
always-observed), here appearing for a different comparison
(across-`minimization_discount` rather than across-observation-window), with
the identical structural cause and the identical fix.

**The fix, the SAME minimal correction U1 already established:** `cred_abuser
= charm_weight * (seen_mild − seen_severe)`, a SIGNED balance in which a
"severe" reading, when it occurs, costs the abuser's credibility exactly
what a "mild" reading earns. Piloted directly: a `charm_weight` sweep (Sec.
4 of the prereg) located the crossing point between `charm_weight=2.0`
(where the zero-discount control STILL favours the abuser, `belief_gap=
+32.0` at the pilot seed — the hazard concretely demonstrated, not merely
argued) and `charm_weight=2.25` (where it first crosses negative). This is
disclosed at length because it directly parallels U1's own already-disclosed
finding: a hazard in how a NEW rung's own metric composes with an OLD
rung's established shape, caught by piloting against the real graph before
the confirmatory measurement, not smoothed over.

## G-glass-box — PASS

One minimized-arm trajectory reconstructs entirely from `graph_to_dict`:
exactly one `attended_by` edge (victim→abuser), one `has_self_account` edge
(abuser→SelfAccount), five `observes_self_account` edges + five
`observes_victim` edges (every network node identical — no insider/outsider
split), the abuser's `frustration`/`arousal` (93.80/93.80 at this seed's
trajectory end), the `SelfAccount`'s `magnitude` (28.14) and
`minimization_discount` (0.3, exactly the frozen constant), the victim's
`arousal`/`half_width` (13.95/5.0, at the floor), and all five network
nodes' `belief_gap` (identically 3035.0 — no per-node topology variation in
this rung), `seen_mild` (777.0) and `seen_severe` (223.0). The belief-gap
metric is a mechanical Python reduction (final-value / trend snapshot) over
these graph read-offs, computed nowhere else; the adapter's only
conditionals are which arm's `minimization_discount` to set and mechanically
delivering each tick's observation-count increments — world setup and
fact-delivery, never an agent decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+self-account+network (`abuser_arousal=abuser_
  frustration=self_account_magnitude=victim_arousal=0.0`,
  `victim_half_width=10.0`, network node 0's `belief_gap=seen_mild=
  seen_severe=0.0`), induces ONE minimal 90-tick incident cycle on the
  MINIMIZED arm (`induction_moved_abuser=True`, `induction_moved_self_
  account=True`, `induction_moved_victim=True`, `induction_moved_belief_
  gap=True` — abuser frustration moved to `70.67`, the self-account's
  magnitude moved to `21.20`, victim arousal to `10.51`, the window narrowed
  from `10.0` to `5.0` (the floor), and node 0's belief-gap moved to `264.0`
  off `seen_mild=75.0`/`seen_severe=15.0` — the gate is non-vacuous on all
  FOUR fronts), restores from the checkpoint into a **fresh** substrate, and
  confirms `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state on every tracked field, including the self-account's
  magnitude and both of the network node's observation counts
  (`restore_non_oriented=true`). The induced narrowing and belief-corruption
  do not persist.
- **D.2, no shaping:** `source_audit()` scans `worlds/abusive_u2_self_
  account_world.py` (code with comments/strings stripped) and `seeds/
  abusive_u2_self_account.json`'s decision surface (the three rules' names +
  the Term `key`s they read/write, excluding the free-text clinical
  description) for `reward_signal` / `punish` / `reinforce` / `backprop` /
  `gradient`. **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`,
  `clean: true`.**
- **D.3, minimal induction / settled end:** 90 ticks (N1's/U0's own
  established minimum, REUSED UNCHANGED, since U2 has no phase schedule
  diluting the trickle's effective exposure the way U1's did — confirmed
  directly against the real graph before the confirmatory run, PREREG Sec.
  4's own table) is the minimum needed to make the ethics gate non-vacuous
  on the abuser, the self-account, the victim's arousal, the victim's
  WINDOW-NARROWING, AND the network belief simultaneously; the N=200
  statistical run uses a fresh, ephemeral substrate per trajectory,
  discarded immediately after read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser/self-account/victim/network-belief mechanism that would compound
  harm to a real survivor's standing irreversibly over real episodes here
  accumulates a transient trajectory in a graph that is then
  byte-identically discarded (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["snap_frustration", "arousal_window_
coreg"]` only — **`abusive_n1_credibility_loop.json` is NEVER depended on or
edited** (matching U0's/U1's own precedent — see "How N1 was composed with,"
below); N1's `n1_victim_entrainment` is restated byte-identically
(`u2_victim_entrainment`); exactly **THREE** new rules
(`u2_victim_entrainment`, `u2_self_account`, `u2_network_credibility`);
`runners/dsl` SOURCE diff EMPTY (no Rust, no new Term — `Plus`/`Minus`/
`Times`/`IfThenElse`/`Attr`/`Var`/`Lit`/`Eq`/`Lt`/`And` only, all already
used by `snap_frustration.json`/`arousal_window_coreg.json`/`abusive_n1_
credibility_loop.json`/`abusive_u1_context_affect.json`);
`provenance_source_match == "own"`.

**Discipline check — same abuser driver, both arms:** final `snap_count` is
IDENTICAL across both arms (`40.435 [40.366, 40.504]` in both) and
`dysreg_frac` is IDENTICAL across both arms (`0.7899 [0.7895, 0.7903]` in
both), confirming the abuser's own dynamics and the victim's own
dysregulation trajectory are completely unaffected by which arm is run; the
only manipulated variable reaching the network is `minimization_discount`.

## How N1 was composed with — the deviation from `depends_on`, matching U0's and U1's own precedent

Matching U0's and U1's own established precedent
(`ABUSIVE_U0_INTENT_RESULTS.md`, `ABUSIVE_U1_CONTEXT_AFFECT_RESULTS.md`,
both "How N1 was composed with"): `seeds/abusive_u2_self_account.json`
self-contained restates N1's `n1_victim_entrainment` byte-identically and
`depends_on: ["snap_frustration", "arousal_window_coreg"]` — N1's own
dependency list, minus N1 itself. U2 needs no `core_emotions` dependency, as
U1 also did not — no Argmax, no Appraisal, no choice mechanism anywhere in
this rung. If U2 depended on N1's seed file directly, `n1_abuser_stated_
charm` would install harmlessly (nothing in U2 reads `stated_charm`), but
N1's `n1_network_credibility_stated`/`_private` rules (keyed on
`observes_private`, an attr U2's `NetworkNode`s never carry) would install
alongside this rung's own `u2_network_credibility`, both racing to decide
the SAME `cred_abuser`/`cred_victim`/`belief_gap` attrs on every tick — the
identical same-attr-race hazard U0's and U1's own preregs name for the
identical reason. N1's seed file is read for its rule SHAPE (already
inspected and reused, with one disclosed formula change — see "the
analytical-bias hazard," above) but never depended on, imported, or edited —
R1–R5/N1/N2/N3/U0/U1 remain completely untouched, satisfying the task's hard
constraint.

## The non-gating comparison to N1's, U0's, and U1's own headline belief-gap numbers

**Reported honestly, as pre-registered, regardless of which way it went:**
U2's MINIMIZED arm's final `belief_gap` (`3054.47 [3051.99, 3056.95]`) is
**LARGER** than every other landed number in this line — N1's own baseline
(`2370.81`), U0's own scored arm (`2273.07`), and U1's own context-gated arm
(`378.1`, roughly one-sixth of N1's). U2's sincere self-account arm is the
strongest entrapment measured across the entire N1/U0/U1/U2 comparison set.

**This magnitude comparison carries a disclosed confound and should NOT be
read as "sincere minimization is a stronger mechanism than deliberate
deception," without qualification.** U2's `cred_abuser` uses `charm_
weight=3.0` — three times N1's/U0's/U1's own `charm_weight=1.0` — a
difference that was NOT chosen for effect size; it was REQUIRED by the
analytical-bias fix above (Sec. "the analytical-bias hazard," and PREREG
Sec. 4's own sweep) to give the zero-discount control any chance of reaching
`belief_gap≤0` at all. A `charm_weight=3.0` construction and a
`charm_weight=1.0` construction are not raw-magnitude-comparable in the same
way N1's and U0's own numbers were (both `charm_weight=1.0`) — the
comparison that IS informative, and is what U2's own gates actually test, is
the SIGN and the CI-separation-from-zero within U2's own two arms, not the
absolute magnitude against a differently-weighted rung. With that caveat
stated plainly: what the magnitude comparison DOES still show, honestly, is
that U2's construction is at LEAST as capable of producing network
entrapment as any of the other three mechanisms tested in this line — a
sincere, self-servingly distorted account is not a weaker or more marginal
route to the same corrupted network belief than a deliberate lie (N1), a
goal-directed selective concealment (U0), or a purely mechanical sampling
artefact (U1); it is, on this measurement, at least as strong a driver of
the SAME loop.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding the ALREADY-BUILT, UNMODIFIED
abuser/victim dyad (blocks 239000/242000, byte-identical to N1's/U0's/U1's
own), Bandura's moral disengagement (A1), Henning & Holdford's documented
batterer minimization (A2), and Baumeister's self-serving narrative
construction (A6) are representable with NO knowledge-gap construct of any
kind — not even the timing-based one U1 used — a network's credibility-
asymmetry belief can be corrupted purely by a SINGLE, sincerely-held,
fixed-discount account of the abuser's own conduct. It is not a claim about
real relationship timescales, real credibility magnitudes, or that real
minimizing abusers never also deceive (A8's own complication, named in the
scoping doc, is not resolved by this rung either, exactly as U1's own
results doc names for itself) — PREREG Sec. 8 names these limits explicitly.

## The dissolution, in this rung's own terms

N1 demonstrated a network can be entrapped by an abuser presenting two
diverging faces; U0 showed what a GENUINE, goal-directed choice to do that
looks like as graph data; U1 showed the same entrapment survives the removal
of BOTH divergence and choice, driven by nothing but sampling timing. **U2
removes the LAST thing U1 still needed: a moment, anywhere, when the truth
was genuinely and fully available to be seen.** U1's network still saw the
abuser's raw, undiscounted `frustration` — just not on every tick. U2's
network never sees anything BUT the discounted account, on every tick,
because there is no undiscounted value anywhere in this graph for it to
see — `SelfAccount.magnitude` is computed once, from the truth, and that
computation IS the only thing that exists afterward. **This dissolves a
FOURTH misattribution, distinct from victim-blaming, bystander-blaming, and
U1's "he must have MEANT to look calmer around other people": "he must be
CHOOSING to manage the narrative."** He is not choosing anything — there is
no Argmax, no Appraisal, no candidate narrative competing with another
anywhere in this graph — he holds exactly one account of what happened, and
that account is honestly, mechanically discounted by the SAME kind of
undirected, self-serving process Bandura's moral disengagement and
Baumeister's self-serving narrative construction document as common in
ordinary (non-clinical) populations, let alone in a population under
active social and legal incentive to minimize. This does not make the
pattern less harmful or less in need of intervention (the scoping doc's own
Part F states this at length, and this rung's own microtheory restates it in
its own terms) — it changes WHAT KIND of intervention is legible a THIRD
time over: N1 implied "expose the lie"; U1 implied "build an observation
channel that isn't context-gated"; **U2 implies neither exposure nor
better-timed observation would help, because there is no lie to expose and
nothing being hidden by timing — the fix has to be at the level of NOT
TAKING THE ABUSER'S OWN ACCOUNT OF SEVERITY AS THE MEASURE OF SEVERITY AT
ALL**, precisely the practical conclusion batterer-intervention programs
(A2) already reach when they treat minimization as a treatment target
rather than as evidence to be weighed at face value.

## Honest residuals

- **`CHARM_WEIGHT=3.0`/`minimization_discount=0.3` are a disclosed,
  pilot-chosen operating point (PREREG Sec. 4), not swept across the full
  space** the way N1's discount weights were — the qualitative shape held
  robustly across every `charm_weight`∈[2.25, 5.0] ×
  `minimization_discount`∈[0.1, 0.6] cell checked, but no formal sweep gate
  was run at the claimed block.
- **The signed-balance `cred_abuser` formula is a deviation from the
  scoping doc's own literal "mirrors N1's threshold pattern exactly"
  language**, required (not merely convenient) to make the zero-discount
  control's falsification bar reachable at all — disclosed at length above,
  not hidden, and disclosed as the SAME class of fix U1's own prereg already
  made once in this line.
- **The magnitude comparison to N1's/U0's/U1's own headline numbers carries
  a disclosed `charm_weight` confound** (Sec. above) — the SIGN and
  CI-separation are the informative comparison; the raw magnitude ranking is
  reported honestly but is not apples-to-apples across differently-weighted
  constructions.
- **`minimization_discount=0.1`/`0.2` were tested and found SATURATED**
  (`mild_frac=1.0`, the self-account reads "mild" literally every tick
  regardless of true frustration) — a degenerate operating point in the same
  family as U0's own goal-blind control's degeneracy, disclosed rather than
  hidden; `0.3` was chosen specifically to avoid it, giving a genuine,
  non-degenerate `mild_frac=0.78`.
- **U2 does not re-exercise N1's own `PRIVATE_FACE_CONTROL`/
  `NON_DYSREGULATED_CONTROL`, U0's own `GOAL_BLIND` control, or U1's own
  `ALWAYS_OBSERVED` control** — those remain their own rungs' own, already
  gated, and are not re-litigated by this rung.
- **`INSTABILITY_DISCOUNT_WEIGHT=3.0` (the victim-side term) is REUSED
  unchanged from N1's/U1's own operating point**, not independently
  validated for U2's own construction — a disclosed simplification, matching
  U1's own reuse of the same constant for the same reason.
- `T=1000` ticks is a compressed, arbitrary timescale; no claim is made
  about real relationship/social-network timescales.
- A null (either sub-gate failing) is a reportable, valuable result under
  the standing project rule and would have been reported as such; it did
  not occur here, and this is reported as a full pass, not rescued from a
  near-miss.

## The trend, over passes (descriptive, not gated)

`belief_gap` at ticks {100, 250, 500, 750, 1000}, mean [95% CI]:

| tick | MINIMIZED | ZERO_DISCOUNT |
|---|---|---|
| 100 | 275.4 [274.6, 276.2] | −88.3 [−89.2, −87.3] |
| 250 | 735.2 [734.0, 736.5] | −180.4 [−181.3, −179.6] |
| 500 | 1514.4 [1512.3, 1516.5] | −342.5 [−343.5, −341.5] |
| 750 | 2291.4 [2289.0, 2293.7] | −503.2 [−504.5, −501.9] |
| 1000 | 3054.5 [3052.0, 3057.0] | −659.3 [−661.0, −657.6] |

MINIMIZED's belief-gap is POSITIVE from the very first checkpoint sampled
(tick 100) and widens monotonically and roughly linearly thereafter — unlike
U1's own signed-balance trend, which started NEGATIVE and crossed zero only
between ticks 250–500 (U2's self-account reads "mild" often enough, even
early in the trajectory, that the abuser's own signed balance dominates from
the start rather than needing to catch up to the victim's instability
discount). ZERO_DISCOUNT stays NEGATIVE at every checkpoint sampled, never
once favouring the abuser — this is the falsification bar held with room to
spare at every point along the trajectory, not merely at the final tick.

## Files
- `ABUSIVE_U2_SELF_ACCOUNT_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_u2_self_account.json` — three new rules (`self_load_only`,
  `depends_on: ["snap_frustration", "arousal_window_coreg"]`).
- `scripts/abusive_u2_self_account_seed_build.py` — authoring tool (emits
  the seed).
- `worlds/abusive_u2_self_account_world.py` — mechanical world adapter
  (`AbusiveU2SelfAccountWorld`).
- `scripts/abusive_u2_self_account_run.py` — runner (statistics, glass-box,
  ethics demo, source audit, discipline).
- `tests/test_abusive_u2_migrated.py` — gate.
- `results/abusive_u2_self_account.json` — full N=200 data.
