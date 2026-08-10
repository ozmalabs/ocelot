# COGNITIVE CAPABILITIES PLAN — the DF/game mechanics reviewed against cognitive science

The DF and governance mechanics are *surface expressions* of a small set of **general
cognitive capabilities** that cognitive science names and models. Bigville is already a
cognitive architecture (it references MicroPsi, the window of tolerance, Bowlby/Erikson
internal working models, theory of mind, and a collapse-based decision core — see the
project memory). This plan strips the game skins off and specifies the *real* capabilities
to build for the agent-based layer, each grounded in a named model and each a graph-native
rung under the substrate's collapse loop.

Sources fetched and read directly (Wikipedia, July 2026) unless flagged as canonical
knowledge (no article / primary text not fetched).

## The review: mechanic → capability → cognitive-science grounding → bigville status

| Game/DF mechanic | General cognitive capability | Grounding | Bigville today |
|---|---|---|---|
| Needs taxonomy | **Motivation: drives + modulators** | Self-Determination Theory (Deci & Ryan: innate psychological needs — competence, autonomy, relatedness); Dörner **Psi theory** / Bach **MicroPsi** (urges + modulators) | hunger/energy/sleep + a curiosity drive; **no unified drive+modulator core** |
| Focus (skill multiplier) | **Attention / cognitive control** | **Yerkes–Dodson** (arousal→performance inverted-U); working-memory capacity (Cowan/Baddeley) | collapse core + surprise-gate + residual-depth; **no bounded attentional resource** |
| Thoughts / memories | **Episodic memory + appraisal + decay** | Tulving (episodic memory, 1972); **appraisal theory** (Scherer; OCC — Ortony/Clore/Collins); **ACT-R** base-level activation decay (Anderson) | affect + nightly journal; **no appraisal-tagged decaying episodic store driving mood** |
| Stress / tantrum spiral | **Allostatic load + coping** | **Allostatic load** (McEwen & Stellar, 1993); Lazarus coping; window of tolerance (Siegel) | window + co-regulation + affect spiral + priors — **largely present** |
| Strange mood → artifact | **Intrinsic motivation / curiosity / flow** | SDT intrinsic motivation; Csikszentmihalyi **flow**; computational curiosity (Schmidhuber/Oudeyer) | curiosity drive (explore the under-compressed) — **partly present** |
| Justice: witness→interrogate→conspiracy | **Theory of mind + source monitoring + deception** | ToM (Premack & Woodruff; Wimmer & Perner false-belief); source monitoring (Johnson et al.) | ToM + witnessed-vs-told provenance + drama deception — **present; deception-detection is new** |
| Mandates / recognition / authority | **Social cognition / normative reasoning** | Bicchieri conditional norms; Fiske relational models | the recognition primitive (block 324000) + governance plan |
| Caravan / diplomacy | **Relationship modeling / reciprocity / trust** | attachment/IWM; Trivers reciprocal altruism | directed Bonds — **present** |

**The finding:** bigville already has the *affective-attachment-social* half well (window,
co-regulation, IWM priors, ToM, bonds, curiosity, the collapse decision core). What it
lacks — and what the DF "needs/focus/thought/stress" spine is the game-skin of — is the
**integrated Motivation → Attention → Emotion → Memory (MAEM) core** that ACT-R, MicroPsi,
and LIDA are each built around. That core is the real deliverable; the artifacts, mandates,
and caravans are *applications* of it plus the recognition work, not new capabilities.

## The plan: build the MAEM core as five graph-native rungs

Each rung: a named capability, the model it implements, the `(G,Γ)` build, a falsifiable
gate on the *qualitative signature* (not a tuned number — anti-tuning), the collapse
decision as the agent's own choice. World-fact vs human-frame discipline holds throughout.

### C1 — Motivational core: drives + modulators (Psi/MicroPsi + SDT)
**Capability:** a small set of grounded *drives* whose deficits generate goals, and global
*modulators* that shape all cognition. **Model:** Dörner's Psi theory / Bach's MicroPsi —
urges (physiological + social + cognitive) and modulators (arousal, *resolution level* =
breadth-vs-depth of processing, *selection threshold* = goal-commitment/persistence,
*securing rate* = attention to the environment); SDT's three innate psychological needs
(competence, autonomy, relatedness) as the non-physiological drives.
**Build:** generalize `need_drive_goal` into a `Drive{kind, urge, setpoint}` set —
physiological (energy/food/rest, present) + **competence** (effectance/mastery),
**affiliation/relatedness**, **certainty** (the curiosity drive reframed as
uncertainty-reduction); each drive's deficit mints a fulfilment goal that competes with
work in the existing collapse. Modulators are town-agent globals the drive profile sets and
that the collapse reads.
**Gate:** agents with different drive profiles diverge (a high-affiliation agent seeks
company, a high-competence agent seeks mastery) on the *same* world; modulators change
processing (high arousal → narrow/fast selection); the `=uniform-drives` control collapses
the divergence. *This is the keystone — everything below reads drives/modulators.*

### C2 — Attention as a bounded, arousal-modulated resource (Yerkes–Dodson + WM)
**Capability:** a finite `focus` that gates how much settles per tick and multiplies
outcome quality. **Model:** Yerkes–Dodson (performance is an inverted-U in arousal — rises
then falls); working-memory capacity limits (a few chunks).
**Build:** a per-agent `focus ∈ [0,1]` computed from arousal on the inverted-U and eroded
by unmet drives (C1); `focus` bounds how many goals/percepts the agent's collapse settles
per tick and scales action outcome (a competence multiplier). This is *also a compute
story* — bounded settlement is the substrate's residual→depth budget made a resource.
**Gate:** reproduce the **Yerkes–Dodson inverted-U** — task performance rises then falls as
arousal increases (under- and over-arousal both degrade); unmet drives measurably degrade
outcomes; the falsifier (unbounded focus) removes the curve.

### C3 — Episodic memory with appraisal, decay, and reconsolidation (Tulving + OCC + ACT-R)
**Capability:** events become appraised, decaying memories that drive mood and re-appraise
on recall. **Model:** Tulving (episodic memory — contextual + emotional trace of a
particular event); OCC/appraisal (emotion = appraisal of an event against goals × agency);
ACT-R base-level activation (memory strength decays as a power law of time/use, boosts on
retrieval); memory reconsolidation (a re-activated trace is re-encoded, possibly altered).
**Build:** `Event → EpisodicTrace{content, appraisal (OCC: goal-congruence × who-caused-it
→ an emotion), activation}`; activation **decays (ACT-R)** and **boosts on recall**; current
**mood = aggregate appraisal of active traces**; **rumination** = a surprising/high-arousal
trace re-activates (surprise-gated, present) → re-appraisal → the trace changes
(reconsolidation), and slow accumulation shifts dispositions (facets change with memory).
**Gate:** the **forgetting curve** (trace activation decays, recall reboosts); mood tracks
the currently-active traces, not just the latest event; recall of a trace *changes* it
(reconsolidation); the `=no-decay` control makes every past event weigh equally (wrong).

### C4 — Allostatic load + coping (McEwen + Lazarus) — extend, don't rebuild
**Capability:** cumulative stress wear-and-tear, breakdown past tolerance, and coping.
**Model:** allostatic load (chronic stress accumulates as "wear and tear," degrading the
system); Lazarus coping (appraisal-driven regulation); window of tolerance (present).
**Build:** an `allostatic_load` that integrates C3's negative appraisals over time (not
just momentary arousal); crossing the window → breakdown (withdraw / tantrum→`viol_act` /
collapse, present) and degraded C2 focus; **coping** = an appraisal-driven decision to
seek co-regulation (present) or intrapsychic quarantine (the "intellectualisation =
residual quarantine" the substrate already has). Mostly wires existing pieces to C3.
**Gate:** chronic negative-appraisal load → breakdown even absent an acute trigger;
co-regulation / a wide window absorbs more before breaking; the `=load-resets-each-tick`
control removes the chronic-stress signature.

### C5 — Intrinsic motivation → generativity (SDT + flow + curiosity) — extend
**Capability:** intrinsic drive that, at challenge≈skill, produces creative output.
**Model:** SDT intrinsic motivation; Csikszentmihalyi flow (engagement when challenge
matches skill); computational curiosity (reward = learning progress / compression gain).
**Build:** reframe the curiosity drive (C1's certainty urge) as intrinsic motivation with a
**flow** condition (a `Drive` satisfied by acts whose difficulty ≈ the agent's competence);
at sustained flow a **generative act** mints a named creation whose content encodes the
maker's dominant active traces (C3) — the DF "artifact," now a cognitive output, and its
*value is recognized* (the recognition primitive), not intrinsic.
**Gate:** flow occurs only when challenge≈skill (too-easy → boredom drive, too-hard →
anxiety/load, C4); generative output emerges under sustained intrinsic drive; a creation's
worth is a recognizer count, not a fixed number.

### Applications (existing capabilities — build as uses, not new cores)
- **Justice depth** = ToM + **source monitoring** (was I a witness or told? — present) +
  **deception/deception-detection** (a genuinely new sub-capability: an agent models that
  another may be misrepresenting, and updates trust) applied to the recognition-gated court.
- **Mandates/authority** = normative/social cognition — the governance plan's recognition
  migration.
- **Diplomacy** = reciprocity/trust over Bonds — extend the wider-world faculty.

## Positioning: where this sits in cognitive architecture

The substrate's **collapse loop is the "cognitive cycle"** (the ACT-R/LIDA production/
settlement step). C1 (drives+modulators) is the MicroPsi/Psi motivational layer; C2 is the
attention/central-executive; C3 is declarative/episodic memory with ACT-R-style activation;
C4 is the affective-regulation layer; C5 is intrinsic motivation. Together they make each
bigville agent a *general* cognitive agent — not a scripted townsperson — which is the
substrate's stated identity. Newell's cognitive-architecture criterion (fixed structures +
knowledge → intelligent behaviour across environments) is the bar: these five are the fixed
structures; the seeds are the knowledge.

## Discipline & honesty

- **These are MODELS.** Gate the *qualitative signatures* science established — the
  Yerkes–Dodson inverted-U, the forgetting curve, drive-profile divergence, chronic-load
  breakdown, flow-at-challenge≈skill — never a tuned target number (anti-tuning). Each rung
  ships its `=off` control as the falsifier.
- **The world-fact/collapse discipline holds:** drives/appraisals/focus are the agent's own
  held state that its collapse reads; nothing is fired on a global tick; a body dying stays
  a world-fact.
- **Source caveats:** appraisal theory, SDT, ACT-R, Yerkes–Dodson, episodic memory,
  allostatic load, and cognitive architecture were fetched and read
  ([en.wikipedia.org](https://en.wikipedia.org/wiki/Cognitive_architecture) and the
  per-topic pages). **MicroPsi has no Wikipedia article**; it is attributed to Dörner's Psi
  theory and Bach's *Principles of Synthetic Intelligence* (MicroPsi) from canonical
  knowledge + the project's own memory, not a fetched page — verify against Bach's book
  before quoting specifics. OCC is Ortony, Clore & Collins (1988); Cowan/Baddeley,
  Csikszentmihalyi, Tulving-1972, Johnson source-monitoring, and the ToM false-belief
  literature are canonical citations, not re-fetched primary texts.

## Build order

**C1 first** (the motivational keystone every other rung reads), then **C3** (episodic
appraisal memory — the other half the DF spine needs), then **C2** (attention ties C1+C3 to
performance and gives the Yerkes–Dodson gate), then **C4** (extend affect to allostatic
load), then **C5** (intrinsic-motivation generativity). Justice/mandate/diplomacy
applications follow the governance plan. Each is a standalone prereg→build→gate rung; the
`.so` stays untouched (graph data + existing DSL Terms).
