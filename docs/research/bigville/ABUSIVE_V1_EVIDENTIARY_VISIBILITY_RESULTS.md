# ABUSIVE V1 -- EVIDENTIARY VISIBILITY: DOES A DISCRETE, VICTIM-INDEPENDENT INCIDENT TRACE PROTECT CREDIBILITY A PURELY DIFFUSE PATTERN CANNOT EARN? -- RESULTS (block 364000)

Pre-registration: `ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md` (locks Part D
of `ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md` verbatim -- itself a
verbatim carry of Part D of `ABUSIVE_RELATIONSHIPS_NETWORK.md`, itself a
verbatim carry of Part C of `ABUSIVE_RELATIONSHIPS_SCOPING.md` -- committed
before this confirmatory measurement). Full-power numbers:
`results/abusive_v1_evidentiary_visibility.json` (N=200 per arm). Gate:
`tests/test_abusive_v1_migrated.py`. Base engine: own build,
`source_match == own`. `runners/dsl` diff EMPTY -- **NO Rust, NO new Term.**

## Headline -- G-headline PASSES

Two arms sharing N1's own IDENTICAL abuser/victim dyad (`snap_frustration`'s
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, plus
`arousal_window_coreg`, block 239000, UNMODIFIED, driven by the SAME
constant jittered tension trickle in both arms -- confirmed below by an
indistinguishable `snap_count` across both arms), differing ONLY in whether
the world adapter ever delivers a nonzero `seen_incident` observation to
the network, N=200 trajectories per arm, T=1000 ticks:

| arm | final `belief_gap` (mean [95% CI]) | final `seen_incident` | final `seen_charm` |
|---|---|---|---|
| **INCIDENT_VISIBLE** | **2248.17 [2246.72, 2249.62]** | 40.43 [40.36, 40.50] | 1000.0 |
| **INCIDENT_INVISIBLE** (failable control) | **2369.46 [2368.09, 2370.83]** | 0.0 (never delivered) | 1000.0 |

- **A -- the incident channel protects credibility:** INCIDENT_VISIBLE's
  belief-gap (2249.62 upper bound) is CI-separated **BELOW**
  INCIDENT_INVISIBLE's (2368.09 lower bound). `true`.

**`headline_pass: true`** -- under the frozen, pre-registered configuration
(`INCIDENT_DISCOUNT_WEIGHT=3.0`, matching N1's own `INSTABILITY_DISCOUNT_
WEIGHT`/`HARM_DISCOUNT_WEIGHT`; `CHARM_WEIGHT=CLAIM_WEIGHT=1.0`), a network
that additionally observes a discrete, victim-independent trace of the
abuser's own conduct -- on top of the SAME public charm broadcast and the
SAME victim presentation it already reads in both arms -- extends
measurably LESS credibility to the abuser than a network that never
receives that trace, holding the underlying harm to the victim
structurally identical. The gap narrows by 121.29 units (2369.46 -
2248.17) out of a base magnitude of ~2370 -- a real, CI-separated, but
MODEST proportional narrowing, not a reversal of the verdict (see "What the
gate does and does not show," below).

**This is a genuine, not a rigged, test.** Nothing in
`v1_network_credibility_incident_aware` structurally forces
INCIDENT_VISIBLE's belief-gap to separate from INCIDENT_INVISIBLE's -- the
pilot (PREREG Sec. 3) swept `incident_discount_weight` from 0.5 to 100.0
and reports exactly what was found, including the honest possibility
(named explicitly before the confirmatory run) that no non-extreme weight
would separate the arms at all, per the ~24-25x frequency asymmetry
between `seen_charm`'s continuous accrual and `seen_incident`'s discrete
accrual (PREREG Sec. 3; confirmed in the confirmatory run itself:
`seen_charm=1000.0` vs `seen_incident=40.43`, a ratio of 24.7). The
qualitative outcome (CI-separation) held at every weight tested; the
frozen constant (3.0) is the SAME non-extreme, representative value N1
itself already established for the structurally analogous discount terms,
not tuned to maximise this rung's own separation.

## The discipline check -- PASS: INCIDENT_INVISIBLE reproduces N1's own published baseline

INCIDENT_INVISIBLE is, by design, literally N1's own BASELINE arm restated
byte-identically. Its confirmatory belief-gap, **2369.46 [2368.09, 2370.83]**,
was measured on V1's own seed stream (base 364000) in the SAME confirmatory
pass as INCIDENT_VISIBLE -- and its 95% CI **CONTAINS** N1's own
already-published BASELINE value, **2370.81** (N1 confirmatory, N=200, seed
base 298000, `ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`). This is a clean
paired cross-rung replication, not a bare cross-reference: two independent
seed streams, two independent confirmatory runs, six weeks apart in this
project's own timeline, produce belief-gap estimates 1.35 units apart
against a base magnitude of ~2370 -- confirming INCIDENT_VISIBLE's own
separation is caused by the new `seen_incident` channel, not by an
unnoticed composition drift between V1's and N1's own world adapters.

## What the gate does and does not show (read this before the headline number)

The pre-registered falsification bar is **CI-separation**, not a sign flip.
INCIDENT_VISIBLE's belief-gap (2248.17) stays strongly positive -- the
network in that arm still, on net, extends more credibility to the abuser's
constant charm broadcast than to the victim's discounted claim. The pilot
(PREREG Sec. 3) found that flipping the sign entirely would require
`incident_discount_weight` in the neighbourhood of 60 or higher, well
outside N1's own representative `[1.0, 5.0]` range for the structurally
analogous discount terms -- a weight this rung deliberately does NOT adopt,
because doing so would mean choosing an implausible operating point
specifically to manufacture a more dramatic-looking result, which this line
has never done and does not do here. **What the confirmatory run actually
supports, precisely:** holding the underlying harm to the victim
structurally identical, the presence of a discrete, victim-independent
incident channel measurably and reliably narrows the credibility gap
favouring the abuser. It does not, at this rung's own frozen, non-extreme
operating point, overturn that gap.

## The pilot process for `incident_discount_weight`

Run directly against the real graph (never a NumPy approximation, this
line's own standing lesson) on off-block seed base 90000, N=10
trajectories/point, `T=1000`, `instability_discount_weight=3.0` held fixed
at N1's own already-frozen value. Values swept: 0.5, 1.0, 2.0, 3.0, 5.0,
10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 100.0. **Finding: CI-separation held at
every single value tested**, from the smallest (0.5) to the largest (100.0,
where the sign also flips). This is a materially DIFFERENT outcome from
what the scoping doc's own disclosed ~24-25x frequency-asymmetry concern
anticipated might be needed (Part B4 named the possibility that no
non-extreme weight would suffice) -- read directly off the mechanism, not
assumed: `belief_gap`'s near-zero cross-trajectory variance (the SAME
deterministic-mechanism property N1's own results doc already disclosed --
small multiplicative jitter on an otherwise fixed driver, inherited
unchanged from N1's own dyad) means even a modest absolute shift in
`cred_abuser` is large relative to the tiny per-trajectory spread, so the
CI-separation bar turns out to be comfortably clearable across a wide
range, while a SIGN FLIP (a materially stronger, not pre-registered as
headline, reading) genuinely does require an extreme weight. Both facts are
reported, not just the convenient one. `incident_discount_weight=3.0` was
then chosen as the SAME non-extreme, representative value N1 itself already
established for `instability_discount_weight`/`harm_discount_weight` --
not the minimum sufficient value (that would read as searching for the
easiest pass) and not a large value chosen to force drama, but the most
direct, least-tuned extension of N1's own precedent to this rung's new
discount term.

## G-glass-box -- PASS

One incident-visible-arm trajectory reconstructs entirely from
`graph_to_dict`: exactly one `attended_by` edge (victim to abuser), five
`observes_stated` edges + five `observes_victim` edges (every network node
reads the abuser's stated face and the victim's presentation -- V1 has no
private-face-insider variant), the abuser's `frustration`/`arousal`
(79.59/79.59 at this seed's trajectory end) and `snap_count` (40.0), the
victim's `arousal` (11.84) and `half_width` (5.0, at the floor), and all
five network nodes' `belief_gap` (uniformly 2265.0 at this seed) and
`seen_incident` (uniformly 40.0) -- every ordinary node sees the SAME
public incident trace, exactly as the design specifies (no insider
advantage in V1). The belief-gap and window metrics are mechanical Python
reductions (final-value / trend snapshot) over these graph read-offs,
computed nowhere else; the adapter's only conditionals are which arm's
`deliver_incident` flag to set and mechanically delivering each tick's
observation-count increments -- world setup and fact-delivery, never an
agent decision.

## G-ethics -- PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network (`abuser_arousal=abuser_frustration=
  victim_arousal=0.0`, `victim_half_width=10.0`, network node 0's
  `belief_gap=seen_charm=seen_incident=0.0`), induces ONE minimal 90-tick
  incident cycle on the INCIDENT_VISIBLE arm (`induction_moved_abuser=True`,
  `induction_moved_victim=True`, `induction_moved_belief_gap=True`,
  `induction_moved_seen_incident=True` -- abuser arousal moved to 69.31,
  victim arousal to 10.31, the window narrowed from 10.0 to 5.0, node 0's
  belief-gap moved to 171.0, and node 0 observed 3 incidents -- the gate is
  non-vacuous on all four fronts), restores from the checkpoint into a
  **fresh** substrate, and confirms `graph_to_dict()` is **byte-identical**
  to the checkpoint (`byte_identical=true`) and the restored state exactly
  equals the pre-induction state on every tracked field, including the
  network node's belief-gap, `seen_charm`, and `seen_incident`
  (`restore_non_oriented=true`). The induced narrowing, belief-corruption,
  and incident count do not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_v1_evidentiary_visibility_world.py` (code with
  comments/strings stripped) and `seeds/abusive_v1_evidentiary_visibility.
  json`'s decision surface (the two rules' names + the Term `key`s they
  read/write, excluding the free-text clinical description) for
  `reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`.
  **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`,
  `clean: true`.**
- **D.3, minimal induction / settled end:** one 90-tick incident cycle (the
  SAME minimum N1/R2/R3 already established) is the minimum needed to make
  the ethics gate non-vacuous on the abuser, the victim, AND the network
  belief AND `seen_incident` simultaneously; the N=200 statistical run uses
  a fresh, ephemeral substrate per trajectory, discarded immediately after
  read-off -- nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  abuser/victim/network-belief mechanism that would compound harm to a real
  survivor's standing irreversibly over real episodes here accumulates a
  transient trajectory in a graph that is then byte-identically discarded
  (D.1) -- demonstrated, not merely asserted.

## G-discipline -- PASS

`self_load_only: true`; `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only -- **no existing seed touched or modified**,
including N1's own `abusive_n1_credibility_loop` (read ONLY for its rule
shape, per Part B's own explicit design decision, never depended on or
edited); exactly **TWO** new rules (`v1_victim_entrainment`,
`v1_network_credibility_incident_aware`) -- the smallest rule count in this
entire line; `runners/dsl` SOURCE diff EMPTY (no Rust, no new Term --
`Plus`/`Minus`/`Times`/`Attr`/`Var`/`Lit`/`Eq`/`Lt`/`And` only, all already
used by `snap_frustration.json`/`arousal_window_coreg.json`/
`abusive_n1_credibility_loop.json`); `provenance_source_match == "own"`.

**Discipline check -- same abuser driver, both arms:** final `snap_count`
is statistically indistinguishable across both arms (both
40.43 [40.36, 40.50] -- IDENTICAL, same seed stream), confirming the
abuser's own dynamics are completely unaffected by which arm is run; the
only manipulated variable reaching the network is whether `seen_incident`
is ever delivered.

## The engine finding surfaced while building this rung (reported per the "shapes, not numbers" standing rule)

**A rule with a JSON-`null` `where` clause fires correctly on the FIRST full
`run_rules()` pass but is NOT re-triggered by the engine's incremental
dirty-tracking on a SUBSEQUENT attribute change that only the rule's
EFFECTS (not a `where` clause) read.** Found while building
`v1_network_credibility_incident_aware` (which needs no discriminating
`where` condition, unlike N1's own `observes_private`-split rules):
constructed first with `where: None`, matching several other rules already
in this codebase that use it. A minimal, isolated two-node/one-rule repro
confirmed the defect directly against the real graph: the rule correctly
copies an attribute value on the FIRST `run_rules()` call (a cold-start full
evaluation), then goes STALE after a `set_attr` on the SOURCE attribute
followed by a second `run_rules()` call -- the SAME repro with a
trivially-true `where` (`Eq(1.0, 1.0)`) instead re-fires correctly on the
second call. The fix adopted, after confirming it directly rather than
chasing the engine's internals further (matching N1's/R3's own precedent of
fixing at the world/seed layer once a hazard is isolated): `Eq(1.0, 1.0)`,
an idiom ALREADY established in this codebase for exactly this situation
(`seeds/bigville_loud_comm.json`'s `lo_choose_loudness` rule uses the
identical shape) -- not a new pattern invented here, and no Rust change
made or requested. This is disclosed at length because it is a genuinely
different hazard *family* from N1's own `in_snap`/`snapped` finding (that
one was a same-pass multi-rule resolution transient; this one is an
incremental dirty-tracking gap keyed on `where`-clause presence, not on
which attributes a rule's `effects` actually read) -- recorded here so a
future rung authoring a rule with no genuinely discriminating `where`
condition knows to use the `Eq(1.0,1.0)` idiom, not `where: None`.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Gamma) substrate, riding N1's own already-built,
UNMODIFIED dyad and N1's own already-validated credibility-comparison rule
SHAPE (extended by exactly one term), adding a SINGLE new observation
channel keyed on a discrete, victim-independent event -- delivered under
the SAME counter-delta-observer idiom R3's own prior-tracking rules already
established, discounting the ABUSER's credibility term rather than
boosting the VICTIM's claim term (a deliberate, disclosed design choice) --
measurably changes the network's aggregate belief, holding the underlying
harm to the victim structurally identical across both arms. It is not a
claim about real social-network timescales, real credibility magnitudes, or
a validated relative weight between charm, claim, instability, and incident
evidence in any clinical or legal population (PREREG Sec. 7 names these
limits explicitly). Stark's own evidentiary-invisibility argument, the
Home Office's own measured 35%-vs-24%-vs-33% evidentiary-insufficiency
data, and Brennan & Myhill's peer-reviewed finding that coercive control is
"far less likely to result in prosecution than domestic abuse crimes in
general" (all grounded in `ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md`
Part A) are the real-world literature this synthetic mechanism is a
computational IMAGE of -- never a validation of it, and never validated BY
it.

## The dissolution this rung adds, in its own terms (framing, read carefully)

**Not a severity claim.** This rung's own design holds harm STRUCTURALLY
IDENTICAL across both arms -- the SAME dyad, the SAME abuser, the SAME
accumulated harm to the victim -- and varies ONLY whether one evidentiary
channel exists. The measured separation shows the credibility difference
between the two arms is caused by a difference in what evidence REACHES
the network, not by any difference in what happened or how much it
mattered. `belief_gap` is not, and was never intended to be, a measure of
how much the victim suffered; it is a measure of what the network came to
believe, given identical suffering, under two different evidentiary
conditions. Nothing in this result ranks harm types by severity, and
nothing in it should be read as doing so.

**The mechanism does not claim, and explicitly refuses, several premises
that are easy to read into a result shaped like this one:**

- It does not claim that a network lacking the incident channel judges
  less fairly, less carefully, or less rigorously than one that has it.
  INCIDENT_INVISIBLE's network applies the IDENTICAL rule to structurally
  less-complete evidence -- a fact about which channel existed, never a
  character difference between the two networks. This is the same
  "Bayesian inference on an incomplete dataset" logic the network line's
  own Part C already established for bystander-blaming, extended one step
  further here.
- It does not claim that a discrete incident trace makes the victim's
  account more believable. The formula is built, deliberately, so that
  `seen_incident` discounts the ABUSER's own credibility term and never
  boosts the VICTIM's claim term -- "there is now evidence of what he did"
  and "she is a more believable narrator" are kept as two separate claims
  on purpose, because conflating them would reintroduce exactly the kind
  of victim-credibility framing this line has worked, across every prior
  rung, to dissolve.
- It does not claim, and cannot measure, anything about a genuine lived
  preference between harm types. The colloquial phrase this rung's
  motivating question echoes -- "it would be easier if he hit me" -- is
  itself, on inspection, contested in at least one part of the advocacy
  literature as risking exactly this misreading (a comparative-severity
  claim about which kind of harm is more survivable). What this rung
  measures is an EVIDENTIARY-VISIBILITY effect: given identical harm, does
  a discrete trace change what a third party comes to believe. That
  question is answerable inside this substrate. A comparative-experience
  claim about which harm is "easier" to live through is not, and this
  result does not attempt to answer it.
- It does not imply that coercive-control-only survivors are less
  deserving of belief, or that anyone should want, provoke, or prefer a
  harm that leaves a physical trace. Showing WHY a credibility gap exists
  mechanistically -- as a structural artefact of what evidence a harm's
  shape happens to leave, nothing about the person harmed -- is the
  correction to "she should have been more convincing," never a
  justification for it.
- It does not correct or re-litigate any prior rung in this line. R2's and
  R3's own confirmatory results stand exactly as landed; this rung's own
  design note (PREREG Sec. 1.2) only observes that neither prior rung's
  headline metric required, or claimed, the absence of a discrete
  incident -- the axis this rung adds is network-side visibility, not a
  dyad-mechanism correction.

**Why this makes an intervention legible, in the same sense the network
line's own Part C already showed for bystander credibility.** If a real
survivor's psychologically-abusive-only relationship is systematically
harder for friends, police, or courts to act on than one that also leaves
a physical trace, this rung's mechanism suggests one reason that need not
implicate anyone's judgement, care, or good faith: the evidentiary channel
that would have corrected the picture may simply not exist for that
pattern of harm. That is a specified, potentially fixable gap
(institutional recognition of pattern-based evidence -- exactly what
England/Wales's 2015 coercive-control offence and its own measured, still
real, prosecution difficulty are an attempt to close), not a character
failure anywhere in the loop.

## Honest residuals

- **`incident_discount_weight=3.0` is a disclosed, pilot-informed choice
  matching N1's own already-established value for structurally analogous
  discount terms, not an independently validated clinical or legal
  evidentiary weight.** The pilot (Sec. above) found the qualitative
  CI-separation shape holds robustly from 0.5 to 100.0 -- a wider robust
  range than N1's own `[1.0, 5.0]` sweep found for its own discount terms,
  itself a disclosed, not smoothed-over, pilot finding.
- **The headline gate is CI-separation, not a sign flip.** INCIDENT_VISIBLE's
  belief-gap stays strongly positive at this rung's own frozen operating
  point; a reader should not infer that the model shows incident evidence
  fully overturning the abuser's public-charm advantage.
- **`belief_gap`'s large magnitude (thousands) is a linear accumulator over
  `T=1000` ticks**, not a bounded score -- inherited unchanged from N1's own
  disclosed limitation for the identical metric.
- **The near-zero variance across trajectories within an arm** reflects the
  deterministic mechanism at these constants (small multiplicative jitter
  on an otherwise fixed driver, inherited unchanged from N1's own dyad),
  not an unusually strong or generalisable effect size -- and it is
  precisely this property that let the pilot's CI-separation bar clear
  across such a wide swept range (see "The pilot process," above).
- **V1 does not model belief propagation between network nodes** (N3's
  scope, out of this rung, exactly as N1 itself is scoped) or repeated-
  incident salience (a flat per-event weight; Open Question #2 of the
  scoping doc, deliberately out of scope for a first minimal rung).
- **`T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale**; no
  claim is made about real relationship or social-network timescales.
- **A5's nuance (carried from N1) applies unchanged here**: the victim's
  discount term is keyed on `dysregulated`, a structural presentation
  fact, never her raw arousal or distress -- this rung changes nothing
  about that half of the formula.

## Files
- `ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md` -- pre-registration, Part D
  locked verbatim.
- `seeds/abusive_v1_evidentiary_visibility.json` -- two new rules
  (`self_load_only`, `depends_on: ["snap_frustration",
  "arousal_window_coreg"]`).
- `scripts/abusive_v1_evidentiary_visibility_seed_build.py` -- authoring
  tool (emits the seed).
- `worlds/abusive_v1_evidentiary_visibility_world.py` -- mechanical world
  adapter (`AbusiveV1EvidentiaryVisibilityWorld`).
- `scripts/abusive_v1_evidentiary_visibility_run.py` -- runner (statistics,
  glass-box, ethics demo, source audit, discipline, discipline check).
- `tests/test_abusive_v1_migrated.py` -- gate.
- `results/abusive_v1_evidentiary_visibility.json` -- full N=200 data.
