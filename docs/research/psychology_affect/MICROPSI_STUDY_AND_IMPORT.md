# MicroPsi / PSI — a precise study, gap analysis, and IMPORT PLAN

**Purpose.** This document is prior-art study turned into a build spec. The
just-landed emotion-framework situating (`EMOTION_FRAMEWORK_LITERATURE.md`, §2.10)
identified **Dörner's PSI theory + Bach's MicroPsi as the near-exact architectural
precedent** for our emotion work: *emotions are not modules, they are configurations
of a small set of global cognitive MODULATORS, driven by a small set of DRIVES, and
an agent lacking them is decision-impaired.* Our 204000 rung instead **authored 11
emotions as explicit appraisal→tendency rules** — a flagged weakness (11 hand-set
appraisals is 11 parameters). This study nails the MicroPsi mechanism precisely so
the next rung can **re-derive emotions as EMERGENT from modulators** (retiring the
authored list) and **import the missing motivational pieces** (chiefly the drive
system and the AFFILIATION drive).

**Posture (unchanged project standard).** This is a study of prior art we will
re-derive and import onto our substrate, **not a novelty claim**. MicroPsi predates
this work by ~20 years and is the honest ceiling for the "emotions as modulator
parameters" architecture. Our contribution remains the integer, glass-box,
byte-identity-gated, shared-atom *instantiation* — not the idea.

Companion: `EMOTION_FRAMEWORK_LITERATURE.md` (the seven-piece situating),
`VISION_CORE_EMOTIONS_RESULTS.md` (204000, the authored set this rung replaces).

---

## 1. MicroPsi / PSI — the architecture, precisely (with sources)

### Sources read

- **Joscha Bach, *Principles of Synthetic Intelligence: PSI — An Architecture of
  Motivated Cognition*, Oxford University Press (2009).**
  <https://archive.org/details/principlesofsynt0000bach> — the book-length treatment.
- **Joscha Bach, "Modeling Motivation in MicroPsi 2," AGI 2015**, LNAI 9205, pp.
  3–13. PDF: <https://agi-conf.org/2015/wp-content/uploads/2015/07/agi15_bach.pdf>
  — the most precise single source on the drive taxonomy, the demand equations, and
  the modulator dynamics. **Primary source for §1.1–§1.4 below; quotations are from
  it.**
- **Joscha Bach, "A Framework for Emergent Emotions, Based on Motivation and
  Cognitive Modulators," *Int. J. Synthetic Emotions* 3(1):43–63 (2012).** Preprint:
  <https://www.goertzel.org/BachEmotionPreprint.pdf> — the explicit
  **modulator→emotion region** mappings (anger, sadness, joy/bliss, fear, angst).
  **Primary source for §1.3.**
- **Dietrich Dörner, *Bauplan für eine Seele*, Rowohlt (1999)** and Dörner et al.,
  *Die Mechanik des Seelenwagens* (2002) — the PSI theory MicroPsi implements
  (German; accessed via Bach's citations and the OpenPsi re-implementation).
- **Joscha Bach, "MicroPsi 2: The Next Generation of the MicroPsi Framework," AGI
  2012**, LNAI 7716, pp. 11–20 — the ReCoN / quad representation.
- Cai, Goertzel et al., **"OpenPsi: Dynamics of a computational affective model
  inspired by Dörner's PSI theory," *Cognitive Systems Research* 17–18:63–80 (2012)**
  — an independent re-implementation (emotions emerge from agent×environment
  interaction; phase transitions in emotional change). Confirms the emergence claim
  is reproducible, not Bach-specific.

### 1.1 The DRIVES / needs — a minimal orthogonal set of demands

PSI/MicroPsi **presupposes no goals**. It presupposes a fixed, minimal, orthogonal
set of **needs (demands)**; goals are *learned* as the situations/actions that
satisfy or frustrate them. "While cognition can change goals, expectations of reward
and priorities, it cannot directly influence the needs itself." The needs do **not**
form a Maslow hierarchy — "all act on the same level," concurrently (polytelic).

**The demand equations (exact).** Each need `d` tracks a variable `c_d` between a
target set-point `v_d` (fully satisfied) and a critical extreme `v_0` (system stops
functioning). When a need arises and cannot be autonomously regulated, it is signaled
by an **urge**:

- **urge strength**: `urge_d = |v_d − c_d|` — the gap from the set-point.
- **urgency**: `urgency_d = |v_d − c_d| · |v_d − v_0|⁻¹` — the gap normalised by
  proximity to the critical extreme (how *pressing* it is).
- Each need carries fixed personality parameters **`weight_d`** (importance vs other
  needs), **`decay_d`** (how fast `c_d` drops toward `v_0` untended), **`gain_d`**
  and **`loss_d`** (reaction to satisfaction / frustration). The tuple
  `[weight, decay, gain, loss]` per need is what makes personality/individual
  variance.
- **Pleasure / displeasure signals** = the *changes* in an urge: a change of `c_d`
  toward `v_d` is a pleasure signal (reinforcement); away is a displeasure signal.
  These are the reinforcers for motivational learning (associators bind urge ↔
  situation/action).

**The three groups** (all concurrent, none prioritised structurally):

| group | needs | how satisfied/frustrated |
|---|---|---|
| **Physiological** | sustenance (food/drink), physical integrity & pain avoidance, rest, thermoregulation, libido | proprioception, hormone/nutrient levels — the survival demands |
| **Social** | **affiliation** (need for recognition/acceptance), internal legitimacy ("honor"), **nurturing** (altruistic care), romantic affection, **dominance** | *legitimacy signals* (smiles, praise) vs *anti-legitimacy* (frowns, reproach) |
| **Cognitive** | **competence** (efficacy), **exploration/certainty** (uncertainty reduction), stimulus-oriented & abstract aesthetics | success/failure at skills; confirmation/violation of expectations |

**The two load-bearing cognitive needs (our closest analogues):**

- **Competence** — task-related (epistemic: success at a skill), effect-related
  (ability to exert change, gain ∝ observed effect size), and **general competence**
  (a compounded running measure of the ability to satisfy needs, used as a heuristic
  to predict success at unknown tasks; low general competence = "lack of
  confidence"). Failure → an urge to *replenish* competence (may cause
  procrastination — pick an easy task).
- **Exploration** — "the need to acquire certainty about objects and processes."
  Confirmation of uncertain expectations *increases certainty and reduces the urge*;
  violations or missing predictions *increase* it. **The strength of the exploration
  urge is used as the heuristic for the degree of uncertainty in the situation.**

**The AFFILIATION drive (the key social import).** Affiliation "is the need for
recognition and acceptance by other individuals or groups. It is satisfied by
legitimacy signals, such as smiles and praise, and frustrated by frowns and
reproach." Its gain scales with the **social weight (reputation) the agent attaches
to the signal's source** (praise from a respected individual > anonymous praise).
"Affiliation plays the role of a **virtual currency**, offering rewards for
cooperative behavior and punishment for defection." **Nurturing** (altruistic care,
gain scaled by social weight of the recipient) is the complement; repeated
affiliation↔nurturing exchange = **bonding**; "**psychopathy may be the result of the
absence of a need for nurturing**." (Note: this directly parallels our 204000
psychopathy = `w_supergraph≈0` knob — see §2.)

### 1.2 The MODULATORS — the exact set

Modulators are **global configuration parameters** of cognition/perception, set by
the urge configuration and by interaction among themselves. **They are not emotions**
— "arousal, valence and aggression are not themselves affects or emotions, but
dimensions of a space of cognitive configurations. **Affects are regions within that
space.**"

MicroPsi "uses currently **six cognitive modulators**." The set is stated slightly
differently across the two papers; both are given here (the union is what matters):

| modulator | what it modulates | what SETS it |
|---|---|---|
| **Valence** | overall positive/negative evaluation | Σ pleasure signals + baseline − Σ displeasure − active urges |
| **Arousal** | energy/effort, action-readiness, reaction speed, sensory-response strength; goal-directedness | **combined strength × urgency of all active needs**; drives resolution ↑ and suppression ↑ |
| **Resolution level** (Auflösungsgrad) | **breadth+depth of processing** — width/depth of activation spreading; high = slow, deep, accurate; low = fast, shallow | ↑ by urgency of the *leading* motive; ↓ by general demand activity; **inversely tied to arousal** (high arousal → fast/coarse) |
| **Selection threshold** (a.k.a. suppression) | **stability of the current motive** — an additive "bonus" to the dominant motive so competitors need to exceed it; anti-oscillation "stubbornness" | ↑ by strength × urgency of the *leading* motive; **↓ by low general competence** (low competence → more flexible/searching) |
| **Securing rate** | **rate of orientation / background checks of the environment** — direction of attention *outward* (perceive) vs *inward* (deliberate) | ↑ by perceived uncertainty (= exploration urge); ↑ by low competence; **↓ by high importance of the leading motive** |
| **Aggression / submission** *(2015 3rd dim)* **OR** **Goal-directedness** *(2012 3rd dim)* | approach vs retract from the attended object (fight/flight); or executive-vs-deliberative balance | aggression ↑ by an agent/obstacle blocking an important motive, ↓ by low competence; goal-directedness ↑ by urgency+arousal, ↓ by uncertainty |

Each modulator additionally has four fixed personality parameters: **baseline**
(default value), **range** (bounds), **volatility** (reaction speed), **duration**
(time to return to baseline). The three "attentional" modulators (resolution,
selection threshold, securing rate) jointly configure attention's **width/detail,
focus, and direction**.

**Note the dependency structure (load-bearing for our emergence rules):** arousal is
the master driver (↑ resolution, ↑ suppression); resolution is ↓ by arousal but ↑ by
leading-motive urgency; selection threshold is ↑ by the leading motive but ↓ by low
competence; securing rate is ↑ by uncertainty & low competence but ↓ by leading-motive
importance. These are the exact update rules the rung will encode.

### 1.3 HOW EMOTIONS EMERGE — regions in modulator × drive space (the load-bearing mechanism)

**This is the mechanism the rung must reproduce.** An emotion is a *characteristic
co-occurrence of modulator settings*, optionally combined with an active drive and a
directedness at an object. From the 2012 and 2015 papers, the specific regions:

| emotion | valence | arousal | resolution | selection-threshold | securing | 3rd-dim / drive | directedness |
|---|---|---|---|---|---|---|---|
| **anger** | negative | **high** | **low** | **high** (strong goal dominance) | **low** (few background checks) | aggression>0, high goal-directedness | at an agent blocking an appetitive goal / causing an aversive one |
| **sadness** | negative | **low** | **high** | — | **low** (few checks) | low goal-directedness | undirected (or "grief" if over a loss object) |
| **fear** | negative | mid | — | — | — | **low competence**, submission | directed at an **aversive** goal |
| **angst / anxiety** | negative | high | — | — | high | **high experienced uncertainty**, low competence, submission | **undirected** |
| **joy** (enthusiastic) | **positive** | **high** | — | — | — | — | pleasure signal / appetitive |
| **bliss** (quiet) | **positive** | **low** | **high** | — | — | — | undirected contentment |
| **jealousy** | negative | — | — | — | — | fear-variant (submission) **or** aggression-variant | at losing romantic/affiliative attachment |

Two axes of emotion:
1. **Undirected emotions** = "typical configurations of the modulators, along with
   competence and experienced uncertainty" (joy, bliss, angst).
2. **Directed emotions** = "a valenced reaction to an object … combined with an
   affective state" (fear at an aversive goal; anger at a blocking agent; grief over
   a loss; pride about an achievement). Directedness **requires the motivational
   system** to supply the object — the modulators alone cannot express "anger *about
   someone*."

The critical property: **the emotion set is not enumerated with per-emotion
parameters. It falls out of a low-dimensional continuous space** (≈5–6 modulators +
active-drive + valence sign). Named emotions are *regions*; the space also yields
*blends* and *subtle distinctions* (enthusiastic joy vs quiet bliss differ only in
arousal + resolution) **for free**. This is the whole reason to re-derive: fewer
parameters (the ~6 modulator update rules + a handful of region boundaries) generate
more affective states (all 11 of ours + blends) than 11 authored appraisal rules.

Independent confirmation: **OpenPsi** (Cai/Goertzel et al. 2012) reproduced this —
emotions *emerge from agent×environment interaction*, with observed trigger →
self-amplification → self-stabilization phase transitions in emotional change. The
emergence is a property of the model, not of one implementation.

### 1.4 The motivational action-selection loop

`demand → urge → motive → intention → action`, with three modes gated by whether a
plan is immediately available (resolution level governs how much attentional
processing is spent):

1. A need becomes active, cannot be autonomously regulated → an **urge signal** fires
   to the reactive layer. Spreading activation along learned urge↔goal associations
   **primes** perception/memory (appetitive goals highlighted, aversive ones flagged).
2. **Opportunistic (automatic) mode**: if an appetitive goal is perceived immediately
   and doesn't clash with current activity, the urge is satisfied opportunistically —
   *no significant attentional processing*.
3. Otherwise the agent tries to **suppress** the new urge by subtracting the
   **selection threshold** (scaled by the strength/urgency of the already-dominant
   motive). If the new urge **overcomes the selection threshold** and exceeds the
   dominant urge, current behavior is **interrupted**.
4. The agent recalls an applicable strategy by spreading activation
   (**associative/automatism mode**); if none is found automatically it engages
   attentional resources to **construct a plan** (**deliberative mode**; MicroPsi2
   uses hill-climbing). If planning fails, it *gives up on the urge and increases the
   exploration need* (→ orientation/experimental behavior).
5. A found plan/automatism = a **motive** (urge + goal + action sequence). **Motive
   strength** = `reward(goal) · urgency · P(success) / cost(plan)`, where `P(success)`
   ≈ task-specific competence + general competence. The **strongest motive is raised
   to an intention** (the new dominant motive) and governs action.

The whole is a **dynamic equilibrium of activities**: needs constantly change, so
goals/priorities are continuously re-evaluated.

### 1.5 Representation + grounding (brief)

MicroPsi agents are **hierarchical spreading-activation networks** of **quad nodes**.
A quad has a central `gen` slot and four typed directional gates from Dörner's PSI:
**`por`** (successor, Latin *porro* — temporal succession), **`ret`** (predecessor,
*retro*), **`sub`** (has-part / downward, *sub*), **`sur`** (part-of / upward,
*super*). `por/ret` encode temporal/causal succession; `sub/sur` encode
partonomy (part-whole). Perception, motor control, memory, and planning are all
spreading activation over these typed links. The modern refinement is the **Request
Confirmation Network (ReCoN)** (Bach & Herger 2015): units with an activation *and a
state*, connected by `sub/sur` (parent↔child) and `por/ret` (predecessor↔successor)
links, that execute/verify hierarchical scripts by request/confirm messages. Learning
is **autonomous and sensorimotor, driven by the drives** — the pleasure/displeasure
reinforcers bind urges to the situations that satisfy them; there is no external
reward channel.

---

## 2. Gap analysis vs the (G,Γ) substrate

Mapping MicroPsi's mechanism onto our landed atoms (196000 `staleness_decay`, 202000
`learning_progress_curiosity` + commit-net, 204000 `core_emotions`, 198000
demotion/LOD, 199000 `disorder_glassbox`).

### 2.1 What we ALREADY have (map our atoms → MicroPsi)

| MicroPsi construct | our atom | map quality |
|---|---|---|
| **Valence** (Σpleasure − Σdispleasure) | 204000 read-off: sign of governing progress/value | **clean** — already the circumplex x-axis |
| **Arousal** (strength×urgency of needs) | 204000 read-off: magnitude of governing surprise/precision | **partial** — we read arousal off a *signal magnitude*; MicroPsi derives it from *drive strength×urgency*. Clean once drives exist. |
| **Certainty / exploration urge** (uncertainty heuristic) | 196000 residual / temporal surprise (`|caught − obs_prev|`) | **clean** — surprise IS experienced uncertainty; exploration urge ≈ our residual |
| **Competence** (efficacy, success-rate heuristic) | 202000 learning-progress (`residual_prev − residual`) | **partial** — learning-progress is the *derivative of surprise-reduction*; MicroPsi general-competence is a *running average of success*. Same family (both efficacy signals); we lack the accumulated running measure. |
| **Selection threshold** (stubbornness bonus, anti-oscillation) | 202000 **commit-net** (`cn_commit`: cut when marginal deliberation value < cost) | **partial** — the commit-net cuts *deliberate-more-vs-act*; the selection threshold is a *bonus to the current motive resisting switching*. Same regress-breaker family; we have the "commit now" half, not the "bonus that resists competitors" half. |
| **Resolution level** (global processing depth) | 198000 demotion/LOD tiers (`dh_tier`: freshness→tier→stored bits) | **partial** — we vary detail **per memory item** (tier by freshness); MicroPsi's is a **global** modulator over all processing. The atom exists; the global scope does not. |
| **Pleasure/displeasure reinforcers** | 196000 residual sign; 204000 value change | **partial** — we have value/progress deltas; not wired as need-satisfaction reinforcers |
| psychopathy = absent nurturing | 204000 `w_supergraph≈0` knob | **clean convergence** — MicroPsi and our 204000 independently land the *same* mechanism |

### 2.2 What MicroPsi HAS that we are MISSING

1. **A first-class DRIVE system.** We have *signals* (surprise, progress, value) but
   no `Drive` node with `target / current / critical / weight / decay / gain / loss`
   and the `urge = |v_d − c_d|`, `urgency = |v_d − c_d|/|v_d − v_0|` equations. This is
   the root missing piece — every modulator is *set by* drive configuration.
   **CONFIRMED against source** (AGI 2015 §2).
2. **Emergent-emotions-from-modulators.** Ours are **authored** (11 per-emotion
   appraisal rules, 204000). MicroPsi's fall out of the ~6-modulator space as regions.
   This is the headline gap the rung closes. **CONFIRMED** (IJSE 2012 §5).
3. **The AFFILIATION (social) drive** — and its complement nurturing. This is what
   *unlocks the social emotions*. 204000 explicitly names guilt/shame as a gap
   ("require the ToM machinery not wired here"); affiliation + a social-weight-scaled
   legitimacy signal is the motivational substrate they hang off. **CONFIRMED**
   (AGI 2015 §"Social Needs").
4. **The RESOLUTION-LEVEL modulator as a GLOBAL knob.** We have per-item LOD (198000);
   we lack a single global processing-depth modulator that arousal/urgency drive.
   **CONFIRMED** — new scope, existing atom.
5. **The SECURING-RATE modulator (vigilance / outward-vs-inward attention).** We have
   `sd_flag_stale` foveation (reads freshness) but no global securing-rate modulator
   that balances perception-vs-deliberation, driven by uncertainty and competence.
   **CONFIRMED** — genuinely new.
6. **The unified demand→urge→motive→intention→action loop** with motive strength
   `reward·urgency·P/cost` and the selection-threshold interrupt. We have pieces
   (commit-net, goals) but not the single motivational spine. **PARTIAL** — the
   deliberation-cut exists; the motive-arbitration loop does not.
7. **Physiological / integrity drives** (energy, pain, rest). Minor for the emotion
   rung but part of the full drive taxonomy; our Doom/walker worlds already have
   proto-versions (time-cost, death-aversion) that could be reframed as drives.

### 2.3 What WE have that MicroPsi does NOT (honest balance)

- **Glass-box, integer-native, gated, reversible discipline.** MicroPsi is
  float-valued spreading activation; ours is exact integer atoms (`Ashr/IDiv/…`),
  default-OFF, byte-identity-gated, with pure-knob reversibility
  (`VISION_DISORDER_GLASSBOX_RESULTS.md`). You can *turn a knob and turn it back
  byte-identically*; MicroPsi cannot.
- **Shared atoms across faculties.** The *same* 196000 freshness atom serves
  perception, memory, curiosity, emotion, and the disorder knobs — one economy, not
  parallel modules.
- **A grounded perception stack** (photon eye, depth-from-motion map, foveation) and
  **physics grounding** (Galileo/conservation from observation). MicroPsi's worlds
  are largely symbolic/Minecraft; its perception is not grounded to this depth.
- **An operationalized STATE-based disorder taxonomy** (199000 + `SUBSTRATE_DISORDER_MAP.md`)
  — disorders as mis-set knobs, reversibly. MicroPsi gestures at this (psychopathy =
  absent nurturing) but does not stage the reversible glass-box.

---

## 3. THE IMPORT PLAN (the actionable deliverable)

Re-derive emotions as EMERGENT from modulators on our substrate, retiring the 204000
authored list. All integer-native, no new Rust Term, default-OFF and byte-identity
gated (the 204000/202000/196000 discipline). One new seed: `seeds/modulators.json`
(depends on `staleness_decay` + `learning_progress_curiosity`), plus a small drive
seed.

### 3.1 The MODULATOR SET to implement (6), each mapped to an atom

Encode as graph rules that read drive state and write modulator attributes on a
`ModulatorState` node (one per `EmotionHub`). Integer, on the same economy.

| # | modulator | attr | update rule (integer, graph-native) | atom source |
|---|---|---|---|---|
| 1 | **valence** | `valence` | `Σ pleasure − Σ displeasure − Σ active_urge` (sign = circumplex x) | 204000 read-off (**have**) |
| 2 | **arousal** | `arousal` | `Σ_d (urge_d · urgency_d)` over active drives (magnitude = circumplex y) | 204000 read-off, now drive-fed (**adapt**) |
| 3 | **resolution level** | `resolution` | `base + urgency(leading) − k·arousal` — **inverse of arousal**, ↑ by leading-motive urgency | 198000 LOD atom, **NEW global scope** |
| 4 | **selection threshold** | `sel_threshold` | `strength(leading)·urgency(leading) − k·(1 − competence)` — bonus to current motive; ↓ by low competence | 202000 commit-net family, **NEW "resist-switch" half** |
| 5 | **securing rate** | `securing` | `uncertainty + (1 − competence) − k·importance(leading)` (uncertainty = exploration urge = residual) | **NEW** (foveation 196000 is the nearest kin) |
| 6 | **competence** | `competence` | running measure of need-satisfaction success; seed from `learning_progress` (`residual_prev − residual`) accumulated | 202000 LP, **NEW accumulator** |

(A 7th, aggression/goal-directedness, is only needed for *anger's directedness* — see
3.3; it reads "blocked valued goal + approachable blocker", which 204000 already
computes.)

**NEW atoms required:** resolution-as-global-modulator (3), the selection-threshold
resist-switch term (4), securing-rate (5), the competence accumulator (6). All
expressible with existing integer Terms (`Plus/Minus/Times/IDiv/Ashr/Max/Min/
IfThenElse/Gt/Lt/And`) — **no Rust.**

### 3.2 The DRIVE additions (graph-native)

A `Drive` node type with attrs `{name, target v_d, current c_d, critical v_0, weight,
decay, gain, loss}` and rules:

- `drive_urge`: `urge = Abs(v_d − c_d)`
- `drive_urgency`: `urgency = IDiv(Abs(v_d − c_d) · SCALE, Max(1, Abs(v_d − v_0)))`
- `drive_decay`: `c_d ← c_d − decay` per epoch (reuse the 196000 scale2 decay atom:
  `c_d = Ashr(c_d, IDiv(now − last_tend, half_life))` — the drive is *literally a
  decaying held quantity*, the same atom).
- `drive_pleasure` / `drive_displeasure`: sign of `Δc_d` → the valence contributions.

**Priority: the AFFILIATION drive** (unlocks social emotions). Seed a `Drive{name:
affiliation}` plus a `legitimacy_signal` ingest (smile/praise → +gain scaled by the
source's `social_weight`; frown/reproach → −loss). Its urge feeds valence and arousal;
its frustration is the appraisal substrate for the social emotions 204000 could not
reach. Add **nurturing** as the complement — and note its absence *is* the 204000
psychopathy knob, giving a second, convergent glass-box realisation.

Minimal set for the emotion rung: `affiliation`, `competence`, `exploration/certainty`
(these three feed all 11 target emotions). Physiological drives (energy/integrity/pain)
are a follow-on that reframes the existing Doom/walker time-cost + death-aversion.

### 3.3 The EMERGENCE MECHANISM — region assignment replaces the authored list

Replace 204000's 11 per-emotion appraisal rules with: **(a) the ~6 modulator update
rules (3.1), then (b) a small set of REGION rules** that read the modulator vector +
active drive/directedness and set `action_tendency`. The region boundaries below
reproduce the 204000 emulation table exactly (same tendency, same valence sign, same
arousal band) but now **derived from modulator state, not authored per emotion**:

| target emotion (204000 tendency) | modulator-region predicate |
|---|---|
| **surprise** (ORIENT) | `arousal` high ∧ `valence`≈0 ∧ `securing` high (orient outward), undirected |
| **fear** (AVOID) | `valence`<0 ∧ `competence` low ∧ aversive-directed ∧ **threat precision decaying** (196000 freshness < t_present) |
| **anxiety/angst** (VIGILANCE) | `valence`<0 ∧ `securing` high ∧ `competence` low ∧ **uncertainty high** ∧ **undirected** (threat precision that *won't* decay) |
| **anger** (APPROACH_BLOCK) | `arousal` high ∧ `resolution` low ∧ `sel_threshold` high ∧ aggression>0 ∧ directed at approachable blocker |
| **frustration** (PERSIST) | as anger but **blocker absent** ∧ engaged (aggression→self/none) |
| **disgust** (REJECT) | contamination appraisal ∧ `valence`<0 (physiological drive) |
| **joy** (REINFORCE) | `valence`>0 ∧ `arousal` high (individual value_progress>0) |
| **bliss** *(NEW blend, free)* | `valence`>0 ∧ `arousal` **low** ∧ `resolution` **high** |
| **sadness** (DISENGAGE) | `valence`<0 ∧ `arousal` low ∧ `resolution` high ∧ goal-directedness low (value falling) |
| **grief** *(NEW blend, free)* | sadness region **directed at a specific loss object** |
| **curiosity** (ENGAGE) | `valence`>0 ∧ exploration urge>0 ∧ **learning_progress>0** |
| **boredom** (LEAVE) | `arousal` low ∧ **learning_progress→0** ∧ engaged |
| **fulfilment** (CONTRIBUTE) | `valence`>0 ∧ **supergraph value>0** (`w_supergraph` gates), distinct from joy |

The **directedness** dimension (fear/anger/grief *at an object* vs joy/bliss/angst
*undirected*) is exactly MicroPsi's directed-vs-undirected split — supplied by the
motive/goal the drive is bound to, not by the modulators alone (§1.3).

**Parameter count drops:** from 11 authored appraisal configurations to **~6 modulator
update rules + ~13 region predicates that share the modulator axes** (fear↔anxiety
differ only by the 196000 half-life; joy↔bliss only by arousal+resolution;
anger↔frustration only by blocker-present). The minimal-pair discriminators 204000
already gates become *automatic consequences of the shared axes*.

### 3.4 THE GATE the rung should use

Pre-register (`MODULATORS_EMERGENCE_PREREG.md`, committed alone first, per project
discipline), then gate:

1. **G-emerge (the headline).** The 11-row 204000 emulation table
   (`VISION_CORE_EMOTIONS_RESULTS.md` §2) reproduces **byte-identically** — same
   expected tendency, same valence sign, same arousal band, one-fire-each, null fires
   none — **but produced FROM the modulator configuration** (drives set → modulators
   computed → region assigned), with **no authored per-emotion appraisal rule
   present**. This is the falsifiable claim: retire the 11 rules, keep the table.
2. **G-blend (free states).** New affective states the authored list did not contain
   fall out of the same modulator space without new rules: **bliss** (positive/low-
   arousal/high-resolution, distinct from joy), **angst** (undirected anxiety),
   **grief** (directed sadness). Show each is a distinct region, not a relabel.
3. **G-social (affiliation unlocks).** With the affiliation drive present, an
   affiliation frustration (anti-legitimacy signal) produces the expected negative-
   valence social appraisal that 204000 could not reach; nurturing-absence reproduces
   the 204000 psychopathy signature *from the drive side* (convergent glass-box).
4. **G-discipline (unchanged bar).** Integer-native (0 non-integer cells across all
   appraisals), default-OFF (every rule guards on `ModulatorState.enabled`; absent it
   every existing path byte-identical), `bash scripts/rung7_vision_bench.sh` BEFORE ==
   AFTER, no Rust / no new Term.
5. **G-minimal-pair (preserved).** The 204000 discriminators still hold *through the
   modulators*: fear↔anxiety by `threat_half_life` alone (now via the securing/decay
   split), anger↔frustration by `blocker_present` alone, curiosity↔boredom by the sign
   of learning-progress alone.

**Honest framing to lead the rung with:** this is *re-deriving Bach/Dörner's
emergent-emotion mechanism on our integer substrate* — the architecture is theirs
(2009/2012/2015). The contribution is the same as always: the glass-box, gated,
shared-atom instantiation, plus the fact that our 11 emotions + blends now fall out of
6 modulators instead of 11 authored rules (fewer parameters, generative blends,
byte-identical to the prior gate).

---

## 4. One-paragraph headline (for the rung brief)

MicroPsi/PSI derives emotions as **regions in a ~6-modulator space** (valence,
arousal, resolution level, selection threshold, securing rate, competence), where the
modulators are **set by a drive system** (`urge = |v_d − c_d|`, `urgency = |v_d − c_d|
/ |v_d − v_0|`; physiological + **affiliation/nurturing** + competence/exploration),
and named emotions (anger = high-arousal/low-resolution/high-threshold/aggression,
sadness = low-arousal/high-resolution/low-goal-directedness, joy vs bliss = same
positive valence differing only in arousal+resolution) are *co-occurrence regions*,
with blends and directed/undirected variants free. **We already hold valence, arousal,
certainty(≈surprise), competence(≈learning-progress), selection-threshold(≈commit-net),
and per-item resolution(≈LOD); we are missing the DRIVE system, the AFFILIATION drive,
global resolution-level, securing-rate, and the emergence-by-region itself.** The
import plan: add a `Drive` node + the affiliation/competence/exploration drives, add
the ~6 modulator update rules (4 new integer atoms, no Rust), and replace 204000's 11
authored appraisal rules with ~13 region predicates over the shared modulator axes —
gated to **reproduce the 204000 emulation table byte-identically from the modulator
configuration** (retiring the authored list) plus new blends (bliss/angst/grief) for
free.

---

*Sources are inline in §1. Primary technical sources: Bach, "Modeling Motivation in
MicroPsi 2," AGI 2015 (drives, modulator dynamics, decision loop) and Bach, "A
Framework for Emergent Emotions," IJSE 3(1) 2012 (modulator→emotion regions), grounded
in Bach, *Principles of Synthetic Intelligence* (OUP 2009) and Dörner's PSI theory
(*Bauplan für eine Seele*, 1999). Our-side atoms: `seeds/staleness_decay.json` (196000),
`seeds/learning_progress_curiosity.json` (202000), `seeds/core_emotions.json` +
`VISION_CORE_EMOTIONS_RESULTS.md` (204000), `seeds/demotion_hierarchy.json` (198000),
`seeds/disorder_glassbox.json` + `SUBSTRATE_DISORDER_MAP.md` (199000).*
