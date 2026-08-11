# How parents teach children language — and how to build the PARENT into the agent's speech world

Research synthesis + build plan. **No code was written; nothing committed.**

The user's correction: *"it isn't all babble."* The current world
(`domains/self_directed_speech_world.py`) is purely self-directed: the agent
picks its own curriculum cell (a graph `Argmax` over deficit), hears speech the
WORLD plays, commits a blind guess, gets a COOKIE iff right, banks the exemplar.
There is no PARENT. Real children do not learn this way. They learn inside a
**dyad**: a caregiver who simplifies, names, tracks the child's level, responds
contingently, and repeats the child's own attempts back correctly. This document
grounds the parental-teaching mechanisms in the developmental-psycholinguistics
literature, maps each to a buildable feature of the world (the PARENT), and gives
a build plan that keeps the project's invariant intact: **the PARENT is the
WORLD/teacher; the agent GROUNDS** (recognition, learning, and the front end stay
the agent's — no donkey).

---

## (1) The parental-teaching mechanisms (cited)

### 1a. Child-directed speech / motherese / IDS
Adults speaking to infants use a distinct register: **slower rate, higher
fundamental frequency, exaggerated/expanded pitch contours, longer pauses,
shorter and grammatically simpler utterances, heavy repetition, a limited
high-frequency concrete vocabulary, and frequent use of the child's name** to
hold attention. IDS measurably aids acquisition: infants attend to and engage
with IDS more than adult-directed speech (ADS), and exposure to more
child-directed speech predicts larger vocabularies. Critically, the benefit is
*developmentally gated*: 21-month-olds reliably learned new words **only** in the
IDS condition, while only those already with larger vocabularies could also learn
from ADS — i.e. the register itself carries the teaching, and its necessity
declines as the learner advances.
([Wikipedia: Baby talk](https://en.wikipedia.org/wiki/Baby_talk);
[Word Learning in Infant- and Adult-Directed Speech, PMC5679190](https://pmc.ncbi.nlm.nih.gov/articles/PMC5679190/);
[The function and evolution of child-directed communication, PMC9116647](https://pmc.ncbi.nlm.nih.gov/articles/PMC9116647/))

### 1b. Joint attention + ostensive naming
Words are grounded to **the referent the child is attending to**. Caregivers
establish *joint attention* (shared gaze/pointing) and **ostensively name**: lift
the target, point, name it — directing the child's attention to the target while
*suppressing competitors*. Tomasello's social-pragmatic account: children use
gaze/point/communicative-intent cues to pick the referent of a novel word.
Experimentally, ostensive naming works primarily by **exogenous attention
direction**: highlighting the target (illuminating it, covering competitors)
produced retention, whereas pointing-only (a pure social cue) left children at
chance — the strongest lever was *highlight the target / reduce competitors*, not
the social cue per se.
([The Right Thing at the Right Time, PMC3314248](https://pmc.ncbi.nlm.nih.gov/articles/PMC3314248/);
[Joint Attention and Vocabulary Development, Akhtar & Gernsbacher](https://gernsbacherlab.org/wp-content/uploads/papers/1/Akhtar_JointAttention_2007.pdf))

### 1c. Scaffolding / Zone of Proximal Development (Vygotsky; Bruner, Wood & Ross)
The ZPD is the gap **between what the learner can do alone and what they can do
with skilled support**. *Scaffolding* (Bruner's term, applying Vygotsky's ZPD) is
the temporary, adaptive support a more-competent other supplies to let the learner
reach a task just beyond their independent level. Its three principles: (i) shared
understanding of the task, (ii) **support that adjusts in-the-moment to how the
learner is performing**, and (iii) **gradual release** of responsibility as
competence grows (the support tapers off). The teacher *tracks the learner's level
and aims teaching just above it* — the opposite of a fixed or self-chosen random
syllabus.
([Zone of proximal development, Wikipedia](https://en.wikipedia.org/wiki/Zone_of_proximal_development);
[Vygotsky vs Bruner, Structural Learning](https://www.structural-learning.com/post/vygotsky-vs-bruner);
[ZPD, Simply Psychology](https://www.simplypsychology.org/zone-of-proximal-development.html))

### 1d. Recasts / expansions / contingent corrective feedback
When a child produces an utterance, the caregiver often **recasts** it: a
contingent, corrected/expanded repetition of the child's own attempt (child:
"doggie run" → parent: "yes, the doggie *is* running"). Recasts are valuable
precisely because they are **contingent on the child's own speech** and therefore
maximally salient (Nelson 1973). The *Contrast theory of corrective input*: adult
models directly contingent on child errors facilitate adult-like competence;
**corrective recasts elicit more correct responses than positive input alone**.
Meta-analysis supports recasts as an effective language-intervention technique.
The mechanism is *contrast*: the child hears its own attempt and the correct form
adjacently, and the difference is the teaching signal — richer than a bare
right/wrong bit.
([Recasts meta-analysis, PMC4450887](https://pmc.ncbi.nlm.nih.gov/articles/PMC4450887/);
[Recasting: a parent-friendly strategy, LG Speech Therapy](https://www.lgspeechtherapy.com/blog/2018/10/8/recasting-a-parent-friendly-strategy-for-language-development);
[Corrective Feedback and SLA, ERIC EJ1086236](https://files.eric.ed.gov/fulltext/EJ1086236.pdf))

### 1e. Contingent responsiveness / serve-and-return
Learning lives in a **dyadic loop**: the child acts (a "serve" — a look, a
babble, a word attempt), the caregiver *responds contingently and promptly* (a
"return") on the child's focus. Contingency (the response is *about what the child
just did/attended to*) and timing are what make the input usable. This is the
loop the recast rides on: the parent's turn is conditioned on the child's turn.
(Same literature as 1d; Nelson's contingency argument.)

### 1f. Acquisition order / the natural curriculum
Acquisition runs through stable stages: **babbling → one-word (holophrastic,
~11–18 mo) → two-word (~18–30 mo) → telegraphic (~2.5 yr+)**. Early vocabulary is
**~50% concrete nouns**, high-frequency, here-and-now; the *naming explosion /
vocabulary spurt* around 18 mo follows the insight that everything has a name. MLU
(mean length of utterance) grows roughly 1 → 2–3 → longer. The curriculum is
**frequency- and concreteness-first, single words before combinations**, and the
parent meters it.
([Stages of language acquisition, Fiveable](https://fiveable.me/introduction-study-language/unit-9/stages-language-acquisition/study-guide/1ctXpb1h0DdV9xyz);
[Major stages of language acquisition](https://englanglanguageacquisition.weebly.com/major-stages-of-language-acquisition.html))

### 1g. Fast mapping
Children form a provisional word↔referent link from **a single (or very few)
exposures** in a constrained naming situation, then refine it with later
encounters. Ostensive naming is what makes one-shot retention reliable in young
children (without it, referent-selection alone did not yield retention).
([The Right Thing at the Right Time, PMC3314248](https://pmc.ncbi.nlm.nih.gov/articles/PMC3314248/))

### 1h. The recast / forward-model angle (the agent's own order-N line)
This connects directly to the agent's existing **order-N analysis-by-synthesis**
frame (memory: *ozma_order_n_analysis_by_synthesis*; "say it to yourself",
"harder speakers take n passes"). A parental recast is *the parent reproducing the
child's attempt, corrected, in the parent's voice* — i.e. an **external forward
model run on the child's hypothesis**. The child hears (its-attempt, correct-form)
as a contrast pair: the same target produced two ways. This is exactly the
instance↔canonical-synthesis comparison that analysis-by-synthesis uses to absorb
speaker/coarticulation nuisance into the forward-model parameters and leave
phonetic identity as the residual. The recast is the *social, external* version of
the agent's own internal AxS loop — and it scales with difficulty (the parent
recasts more, and more slowly, where the child struggles = the adaptive *n*).

---

## (2) Mechanism → buildable feature of the world (the PARENT)

The PARENT is a **world adapter** (per CLAUDE.md: Python translates I/O; it does
not reason). The PARENT's *teaching* may be produced by the in-repo
"LLM-teaches / agent-grounds" plumbing (`domains/llm_partner.py`,
`domains/teacher_hook.py`, the `dict/wiki/phonology` teacher chain) and/or a
structured CDS protocol + the existing TTS (`tts`/`piper_tts`). The agent's
recognition, learning, and front end stay graph-resident and unchanged.

| Mechanism | Buildable PARENT feature | Where it lives |
|---|---|---|
| **CDS / IDS register (1a)** | A `ParentUtterance` produced with IDS prosody: slower rate, raised pitch, expanded contour, inserted pauses, repetition. espeak exposes `-s` (rate) and `-p` (pitch); piper voices give the realistic per-language register. The PARENT speaks the *teaching* clip in IDS, not ADS. | World adapter: a `parent_say(word, lang, register="IDS")` that sets espeak/piper params. The clip is still ingested by the agent's own front end. |
| **Joint attention + ostensive naming (1b, 1g)** | The PARENT delivers (word, clip) **as a labelled naming event with the referent given**: a `NamingEvent` node carrying the word Concept + the clip, with competitors *suppressed* (the candidate set restricted to the few words being taught). This is the "highlight target / reduce competitors" lever — and in the agent's world the "referent" is the word identity, given by the teacher. | World adapter mints the clip; a graph `NamingEvent`/`taught_as` edge ties clip→Concept (the supervised label the agent grounds). The competitor-suppression = the PARENT restricting the active lexicon (a curriculum scope), which the recognizer already supports per-cell. |
| **Scaffolding / ZPD (1c)** | The PARENT **picks the next item at the agent's measured level + ε**, not the agent's deficit-only self-pick. Concretely: a `Parent` node that reads each cell's held-out cookie-rate and selects the cell/word **just above mastery** (ZPD = mastered_floor < rate < mastery_ceiling), and **gradually releases** (as a cell's held-out rate crosses a mastery threshold, the PARENT advances to harder items: more words, then two-word, then noisy/cross-speaker). | Replace/augment the curriculum `PICK_TERM` with a **parent-driven `ZPD_PICK_TERM`**: a graph `Argmax` over cells of a ZPD-band priority (peaks inside the band, low outside) — still a graph Term the agent evaluates; the PARENT only *measures and exposes* the level. |
| **Recasts / expansions / contrast (1d, 1h)** | After the agent's blind guess, the PARENT **re-utters the correct word in IDS** as a `Recast` — *especially on a miss* — so the agent gets (its-guess-clip, correct-form-clip) as a contrast pair to bank, not just a cookie bit. On a two-word attempt, the PARENT expands (re-utters the fuller form). | World adapter `recast(guess, truth, lang)`: synthesize the correct word in IDS, mint a `Recast` clip, bank it as a *high-salience* exemplar of the true Concept (and optionally a `contrast_with` edge to the guess for the agent's AxS/contrast machinery). |
| **Contingent response / serve-and-return (1e)** | The teaching turn is **conditioned on the agent's turn**: the PARENT responds to *what the agent just guessed* (recast the specific confusion), not to a fixed script. | The loop order becomes serve(agent guess) → return(parent recast/next item). Pure adapter sequencing; the decisions stay graph Terms. |
| **Acquisition order / natural curriculum (1f)** | The PARENT's syllabus is **ordered**: concrete high-frequency single words first, then more words, then two-word combinations, then harder sources (noise, real FSDD speakers, cross-speaker). The granularity axis already exists (`digit`/`word`); add the *ordering* + *gating* by mastery. | A `Curriculum` graph structure the PARENT walks in order, advancing only when the ZPD/mastery gate opens. The existing 3-axis cell grid is the substrate; the PARENT supplies the *traversal order*. |

**The in-thesis line (non-negotiable).** The PARENT *provides the teaching*:
scaffolded CDS speech, the naming label, the recast, the adaptive level. The agent
*does the grounding*: it still extracts features through **its own** front end
(`feature_channels` / `domains/agent_frontend`), still recognises with **its own**
many-settings `Argmax`-of-product over exemplars (`blind_guess`), still banks and
still self-designs its ears. **An LLM-as-parent is fine as the teacher** (it can
generate the IDS script, the word list at the right level, the recast wording) —
it is **never** the agent's recognizer. The PARENT speaks; the agent grounds. This
is the same boundary `llm_partner` / `teacher_hook` already enforce ("nothing of
the teacher is stored on the agent").

---

## (3) Build plan — add the PARENT to the self-directed world

### Shape: a PARENT loop wrapping (not replacing) the babble loop
Keep the existing world (cells, `blind_guess`, cookie, `bank_exemplar`, the
front-end self-design, the meta-monitor). Add a **`Parent`** alongside the
`SpeechWorldRoot` that drives a *teaching turn* each step, and turn the loop from
"agent self-picks → world plays → cookie" into a **dyad**:

```
PARENT turn (return):   pick item at agent's ZPD  → ostensively name it in IDS
AGENT turn (serve):     feature_channels → blind_guess  (the agent's own cognition)
PARENT turn (contingent return):  cookie iff right
                                  + RECAST the correct word in IDS (esp. on miss)
AGENT turn:             bank exemplar(s) — the heard clip AND the recast clip
measure:                held-out (unchanged, ungameable) → drives ZPD level
```

### What stays the AGENT's (unchanged, graph-resident)
- **Grounding / recognition**: `blind_guess` (the many-settings `Argmax`-of-product
  over banked exemplars, in feature space). Never inverts TTS, never uses a net for
  recognition.
- **The front end**: `domains/agent_frontend` (the self-designed cues) and its
  plateau/effect-gate/deeper-wall self-direction. The recast clips are ingested
  through the same front end (raw audio banked, re-extracted at the live width —
  the existing design already does this).
- **Learning as admissibility**: cookie/recast = *bank an exemplar* (admissible
  structure), not a gradient reward.
- The **held-out probe** (ungameable) stays the progress yardstick.

### What the PARENT provides (new world-adapter pieces)
1. **`parent_say(word, lang, register)`** — IDS-register TTS (espeak `-s`/`-p`
   slowed + pitched, or a piper voice). Boundary DSP/TTS only.
2. **A `Parent` graph node + `ZPD_PICK_TERM`** — the scaffolded pick. Read each
   cell's held-out rate; select the cell/word **inside the ZPD band**
   (`mastered_floor < rate < mastery_ceiling`) with the most teaching value. This
   is a graph `Argmax` (same pattern as `PICK_TERM`); the PARENT (adapter) only
   *measures the level and exposes it on the cells*. **This replaces the agent's
   deficit-only random-ish self-pick with teaching at the agent's level.**
3. **Ostensive naming as a supervised label** — the clip arrives *with* its word
   Concept (a `NamingEvent`/`taught_as` edge) and a *restricted competitor set*
   (the few words currently being taught), exactly the highlight-target/
   reduce-competitors lever. The agent grounds the given label.
4. **`recast(guess, truth, lang)`** — on each turn (and especially on a miss),
   synthesize the *correct* word in IDS and bank it as a high-salience exemplar of
   the true Concept; optionally mint a `contrast_with` edge guess↔truth so the
   agent's contrast/AxS machinery can use the pair. **This is the richer-than-cookie
   signal.**
5. **An ordered `Curriculum`** — concrete single words → more words → two-word →
   harder sources (noise → FSDD real speakers). The PARENT advances only when the
   mastery gate opens (gradual release).

### How the PARENT ADAPTS to the agent's held-out level (the scaffolding)
The PARENT reads the *same ungameable held-out cookie-rate* the report already
computes per cell, and:
- **selects** within the ZPD band (not the saturated cells, not the impossible
  ones) — the graph `ZPD_PICK_TERM`;
- **advances** (unlocks the next curriculum stage / adds words / harder source)
  when a cell crosses `mastery_ceiling` — gradual release;
- **intensifies** (more recasts, slower IDS, smaller competitor set) where the
  agent is *inside* the band but slow — the adaptive *n* (more passes on harder
  material), the social analogue of the order-N loop.

### How recasts feed learning (richer than the cookie)
Today the cookie is a single bit and only a *correct* clip gets banked. With
recasts, **every turn yields a correctly-labelled IDS exemplar of the true word**
(banked at high salience), and on a *miss* the agent additionally gets the
(guess, truth) **contrast pair**. That is strictly more grounding signal per turn,
and it is *contingent* (about the specific error the agent just made) — the
Nelson/Contrast-theory mechanism.

### Does the PARENT subsume or complement the cookie / curriculum / meta-monitor?
- **Curriculum**: the PARENT's `ZPD_PICK_TERM` **subsumes** the agent's
  deficit-only `PICK_TERM` for the *taught* track. (Honest: keep the self-pick as
  a *secondary*/free-play track — children also self-direct; the literature is a
  dyad of teaching *and* exploration, not pure teaching. Make the PARENT the
  primary curriculum, not the only one.)
- **Cookie**: **complemented**, not removed — the cookie stays as admissibility
  feedback; the recast adds the contrast exemplar on top.
- **Meta-monitor / front-end self-design**: **unchanged and complementary**. The
  PARENT's mastery-gate (advance the syllabus) and the meta-monitor's deeper-wall
  flag (the front end is not the lever here) are different signals; the deeper-wall
  flag is exactly when the PARENT should *stay* on a stage and recast more / slow
  down rather than advance — they compose.

---

## (4) The single highest-leverage first piece

**Build the adaptive scaffolded curriculum + ostensive naming first** — i.e.
replace the agent's deficit-only self-pick with a **PARENT that teaches at the
agent's measured level, giving the word with the clip (supervised label) and a
restricted competitor set.** Concretely: a `Parent` node + `ZPD_PICK_TERM` (graph
`Argmax` over cells inside the ZPD band, fed by the existing held-out rate) + the
ordered curriculum traversal with a mastery gate + `parent_say` in IDS register.

Why this first: it is the **structural** change the user is pointing at ("it isn't
all babble") — it converts the loop from self-directed sampling into a *taught
dyad* — and it reuses the most existing machinery (the cells, the held-out
measure, the recognizer, the front end) with the least new surface. Recasts (the
contrast pair) are the natural **second** piece, layering the contingent
richer-than-cookie signal on top once the scaffolded teaching loop exists. IDS
prosody tuning and two-word/expansion granularity are refinements after that.

---

## Honest flags — what's supported, what's speculative, where "make a parent" risks a donkey

**Well-supported by the literature (build with confidence):**
- IDS aids early word learning and its necessity is *developmentally gated* (1a) —
  so an IDS register + its *gradual release* is sound.
- Ostensive naming's effective lever is **attention to target / suppression of
  competitors** (1b) — so the buildable form (give the label, restrict the
  competitor set) targets the *actual* mechanism, not just "point" (pointing-only
  was at chance). This is a strong, specific result.
- Recasts as contingent corrective input help acquisition (1d, meta-analysis) —
  the contrast-pair feature is grounded.
- The acquisition-order stages and noun-heavy/frequency-first early vocab (1f) are
  textbook-stable.

**Partly speculative / weaker / extrapolated:**
- **Joint attention's** causal necessity is *debated*: Akhtar & Gernsbacher argue
  children also learn words **outside** joint-attention/ostensive contexts (and an
  18-mo study shows non-ostensive learning). So *don't* model the PARENT as the
  **only** path to grounding — keep the self-directed/free-play track. Ostensive
  naming *helps*; it is not the sole route.
- The **recast = forward-model / order-N** mapping (1h) is the agent's own
  theoretical frame, not a claim from the developmental literature. It is a
  *productive analogy* (and consistent with analysis-by-synthesis), but flag it as
  the project's interpretation, not an established psycholinguistic finding.
- Mapping "joint attention to a *referent*" into this world is **loose**: the
  agent has no shared physical scene; the "referent" is the *word identity* given
  by the teacher. That is honest (supervised label) but it is *not* the full
  social-pragmatic grounding children get — it is naming with the answer given.
  Real referential grounding (a shared world) is out of scope here.

**Where "make a parent" risks becoming a donkey (the boundary to police):**
- The agent's **grounding must stay the agent's.** The PARENT may *speak*, *name*,
  *recast*, and *pick the level* — it must **never** do the *recognition*. If an
  LLM-parent ever returns "what the agent heard," or its embedding is used to
  decide the guess, the project has become "a car powered by a donkey." The
  recognizer stays `blind_guess` over the agent's exemplars in its own feature
  space. (`llm_partner`/`teacher_hook` already enforce this: the teacher is a
  pluggable `ask()` channel, nothing of it stored on the agent — reuse that shape.)
- The PARENT's pick is **a graph Term the agent evaluates** (like `PICK_TERM`),
  fed by the agent's *own* held-out measure — not a Python `if`/`else` that decides
  the syllabus. Keep the decision graph-resident; the adapter only measures and
  enacts (CLAUDE.md).
- Don't let the supervised label collapse the difficulty: ostensive naming
  *restricts competitors*, it does not hand over the answer at recognition time —
  the agent must still **guess** the clip; the label is the *learning target*, the
  cookie/recast is the *feedback*. The ungameable held-out probe (no naming, full
  competitor set) stays the progress yardstick, so the teaching cannot inflate the
  measured capability.

---

## Sources
- [Baby talk — Wikipedia](https://en.wikipedia.org/wiki/Baby_talk)
- [Word Learning in Infant- and Adult-Directed Speech — PMC5679190](https://pmc.ncbi.nlm.nih.gov/articles/PMC5679190/)
- [The function and evolution of child-directed communication — PMC9116647](https://pmc.ncbi.nlm.nih.gov/articles/PMC9116647/)
- [The Right Thing at the Right Time: Why Ostensive Naming Facilitates Word Learning — PMC3314248](https://pmc.ncbi.nlm.nih.gov/articles/PMC3314248/)
- [Joint Attention and Vocabulary Development: A Critical Look — Akhtar & Gernsbacher](https://gernsbacherlab.org/wp-content/uploads/papers/1/Akhtar_JointAttention_2007.pdf)
- [Zone of proximal development — Wikipedia](https://en.wikipedia.org/wiki/Zone_of_proximal_development)
- [Vygotsky vs Bruner: Two Approaches to Scaffolding — Structural Learning](https://www.structural-learning.com/post/vygotsky-vs-bruner)
- [Zone of Proximal Development — Simply Psychology](https://www.simplypsychology.org/zone-of-proximal-development.html)
- [The Efficacy of Recasts in Language Intervention: A Systematic Review and Meta-Analysis — PMC4450887](https://pmc.ncbi.nlm.nih.gov/articles/PMC4450887/)
- [Recasting: A parent-friendly strategy for language development — LG Speech Therapy](https://www.lgspeechtherapy.com/blog/2018/10/8/recasting-a-parent-friendly-strategy-for-language-development)
- [Corrective Feedback and Second Language Acquisition — ERIC EJ1086236](https://files.eric.ed.gov/fulltext/EJ1086236.pdf)
- [Stages of language acquisition — Fiveable](https://fiveable.me/introduction-study-language/unit-9/stages-language-acquisition/study-guide/1ctXpb1h0DdV9xyz)
- [Major stages of language acquisition](https://englanglanguageacquisition.weebly.com/major-stages-of-language-acquisition.html)
</content>
</invoke>
