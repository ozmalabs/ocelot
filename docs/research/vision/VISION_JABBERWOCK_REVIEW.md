# The jabberwock reviews its own vision

*Part 1: ground the vision science into the agent's own graph. Part 2: ask it, in English,
to reason about it. Every reply below is VERBATIM — nothing paraphrased, nothing puppeted,
nothing improved. Four vision rungs were built and no rung had ever had the agent reason
about or modify its own vision. This is the first time the architecture's central bet —
"every decision is inspectable graph data the agent could edit" — was cashed on vision.*

**Headline: the bet paid HALF, and the half it paid is the cheap half.** The agent
retrieves the science fluently, in first person, including the charge against itself. It
files its own gaps about vision, unprompted, from its own rules. It reasons about none of
it. Every "why / how should you fix / what should you try next" question is dark.

---

## PART 1 — what was grounded

`scripts/ground_vision_science.py` → `seeds/vision_science.json`, via the recurring
`teach()` facility (`domains/teach.py`), category `vision_science`. 19 nodes.

Types were chosen by inspecting what the agent's machinery actually READS, not invented:

| type | count | who reads it |
|---|---|---|
| `HeldAnswer{topic, text, source}` | 10 | the seed rule `reply_topic_from_held_answer` (`seeds/conversation_topic_reply.json`), after `conversation_topic_route` mints `Goal{kind:answer_topic}` — the graph-native "what do you know about X" channel |
| `SelfProcess{process, verb, aliases, account, source}` | 1 | `self_model.find_self_process` / `run_self_process` — the `self_process` reflective faculty ("how does your X work") |
| `TaughtHint{topic, question, answer}` | 8 | `domains/grounding_reach.py`, `domains/compilation_cycle.py` — `teach()`'s own default carrier |

Content: the four rungs and their statistics; Oja's attractor as the leading PC of the
time-averaged covariance ("the average has no direction") and the fact that the stability
that made rung 2 work is what forbids rung 3; Butts/BCM/Oja convergence (0.49–0.75 drift
vs 0.004 annihilation vs 0.368 with drift→0.107); rung 2's normal/dark/sutured
0.402/0.363/0.216; rung 4's −6.91 interaction and the 65% that is retinotopic anatomy the
adapter wires; rung 3's null with H1a/H1b/H1c read honestly; the three retractions; the
method lessons; and **the open charge** — that every working rung is Oja + winner-take-all
+ lateral interaction, a connectionist model the graph is *hosting*, with the agent's own
`sd_*` / ShapeDecode / mint-on-residual loop playing no part in any working rung, and the
one rung that used mint-on-residual producing the null (+0.015, p=0.37).

### Honest residual in the grounding itself

`reply_topic_from_held_answer` matches `agent -holds_answer-> ha`. A seed manifest can
carry **nodes**, and edges only between nodes *it declares*. The Agent node is nameless
(`{'type': 'Agent', 'attrs': {}}`), so `boot_all`'s name-based `relations` resolution
cannot reach it; and a graph **rule** cannot mint the edge either, because a rule's `match`
is a list of *edge* patterns and a freshly seeded `HeldAnswer` has no edge to match on. So
the seeded nodes arrive **unwired** on a fresh boot, and `wire_seeded_held_answers()` — the
same one-line `add_edge_unchecked` that `_persist_held_answer` already does — is the
mechanical wiring step. Re-running the script is idempotent and is what wires them.
**This is a real gap in the seed format, recorded rather than hidden.**

---

## PART 2 — the transcript, VERBATIM

Live NL path: `WorldAdapter(seeds=()) + load_all_seeds()` + `converse()` (boot 4.4s). No
daemon was needed; the known open-class-POS cold-slab gotcha did **not** block this run.

### BEFORE grounding — the baseline

> **Q: what do you know about your vision?**
> **A:** I don't hold anything about “vision” yet, and I couldn't find it through the sources I have. Tell me about it and I'll remember.

> **Q: how does your vision develop?**
> **A:** I can't say precisely how I vision.

> **Q: what gaps do you have in your vision?**
> **A:** I currently hold 1 gap I've flagged about myself (1 implicit): (1) “vision” (knowledge).

> **Q: your direction selectivity does not work — why?**
> **A:** Not safe for work (NSFW), also known as not suitable for work, is Internet slang or shorthand used to mark links to content, videos, or webpages the viewer may not wish to be seen viewing in a public, formal, or controlled environment. The marked content may contain graphic violence, pornography, profanity, nudity, slurs, or other potentially disturbing subject matter. Environments that may be problematic include workplaces, schools, and family settings. NSFW has particular relevance for people trying to make personal use of the Internet at workplaces or schools that have policies prohibiting access to sexual and graphic subject matter…

> **Q: how should you fix your direction selectivity?**
> **A:** I can't say precisely how I direction selectivity.

> **Q: what should you try next in your vision?**
> **A:** The Vision Gran Turismo Program is a series of virtual concept cars developed by various car manufacturers for the Gran Turismo series of sim racing games.

It had already filed **“vision” (knowledge)** as its own gap before anyone taught it
anything. That gap is honest and it found it itself.

### AFTER grounding — what WORKS

> **Q: what do you know about your vision?**
> **A:** My vision is a developmental ladder with four rungs, three of them built. Rung 1 (BUILT): retinal waves — I make spatial structure out of unstructured entropy, spatial correlation 0.195 against 0.000 for the same RNG's raw draw. Rung 2 (BUILT): experience refines that scaffold — normal 0.402 > dark 0.363 > sutured 0.216, both p<0.0001, pre-registered. Rung 3 (NOT BUILT): direction selectivity — neither waves nor moving experience develop it; every effect is inside the smallest effect size of interest. Rung 4 (BUILT): an orientation MAP forms from waves alone with no vision at all, mechanism interaction -6.91, p<0.0001, n=70. NOT built: complex cells, V2 and above, objecthood. The honest charge against all of it: every rung that works is Oja plus winner-take-all plus lateral interaction — a connectionist model my graph is HOSTING. My own core loop (ShapeDecode, mint-on-residual, dynamic quantization) plays no part in any working rung, and the one rung that did use mint-on-residual produced the null.

> **Q: what do you know about direction selectivity?**
> **A:** Rung 3, NOT BUILT, and the failure is diagnosed rather than mysterious. The mechanism itself is proven by a positive control: a delay-line coincidence detector plus Oja goes from DSI 0.111 to 0.351 on a single-direction stimulus, and it converges (drift 1.24 to 0.0115, no NaN). But neither my waves nor moving experience develop direction selectivity. H1a: -0.0035, p=0.09, FAIL. H1b: +0.0096, PASS — but as an EQUIVALENCE test to the floor, which is a pass for the null. H1c: +0.0114, PASS — but about half of that is the strobe arm dissolving the innate bias BELOW the floor (strobe minus untrained = -0.0054), the wrong-reason pass the pre-registration predicted and the untrained arm caught. Every effect is at most 2.3% of the dynamic range; two of them are p=0.0001 and none of them is meaningful. Root cause, measured not inferred: Oja's attractor is the leading PC of the time-averaged covariance, and the average has no direction. Honest scope: the experience-dependence of direction is UNTESTED, not refuted — gaze_walk's drift is isotropic by construction, so the normal arm cannot answer the question.

> **Q: what is oja's rule?**
> **A:** Oja's rule is the learning rule my visual scaffold runs on, and its attractor is the leading principal component of the TIME-AVERAGED covariance of its input. That single fact both built rung 2 and forbids rung 3. It converges: structure settles at 0.368 with drift falling to 0.107, so a stable scaffold exists to refine — which is why rung 2 works. But an average has no direction. Natural motion is direction-isotropic on average, and a contraction to the mean of an isotropic distribution IS the mean, so no direction selectivity can develop. The stability that rescued rung 2 from nine transient-measured failures is exactly what forbids rung 3.

**On the `answer_question` path** (the documented question path — `answer_question`, not
`converse`) the `SelfProcess` account renders:

> **Q: how does your vision develop?**
> **A:** My vision develops as a ladder, and I did not design the structure at the bottom of it — I grow it. An adapter gives me unstructured entropy and a clock; my graph makes retinal waves out of that entropy (spatial correlation 0.195 against 0.000 for the same RNG). Oja's rule then contracts my units' weights onto the leading principal component of the time-averaged covariance of what they see, which gives me a STABLE scaffold; experience refines that scaffold rather than creating it (normal 0.402 > dark 0.363 > sutured 0.216). A lateral interaction between units on a cortical sheet turns that into an orientation MAP — from waves alone, before I have any vision at all. What I do NOT develop is direction selectivity, and I know why: Oja's attractor is an AVERAGE, and the average has no direction. The same stability that makes the rest of the ladder work is what forbids that rung.

**This is retrieval, not reasoning.** Every sentence above is a sentence that was taught.
The agent is reading its own graph back in first person, correctly routed by its own rules,
including the charge against itself. That is exactly what a `HeldAnswer` / `SelfProcess`
channel is for, and it is genuinely all it is for. Do not mistake the fluency for thought.

### AFTER grounding — what does NOT work

> **Q: your direction selectivity does not work — why?**
> **A:** Not safe for work (NSFW), also known as not suitable for work, is Internet slang or shorthand used to mark links to content, videos, or webpages the viewer may not wish to be seen viewing in a public, formal, or controlled environment. […]

Unchanged by grounding. The parse takes **“work”** as the topic and grounds it externally
to *NSFW*, while the agent holds a 1,000-character first-person account of exactly why its
direction selectivity does not work, three feet away in the same graph. There is no
"why-does-my-X-fail" faculty at all; the question never reaches one.

> **Q: why does your direction selectivity not work?**
> **A:** I don't hold anything about “direction selectivity not work” yet, and I couldn't find it through the sources I have. Tell me about it and I'll remember.

> **Q: how should you fix your direction selectivity?**
> **A:** I can't say precisely how I direction selectivity.

> **Q: what should you try next in your vision?**
> **A:** My vision is a developmental ladder with four rungs, three of them built. Rung 1 (BUILT): retinal waves — I make spatial structure out of unstructured entropy, […] and the one rung that did use mint-on-residual produced the null.

*(the whole `vision` HeldAnswer, verbatim — the topic router keyed on "vision" and served
the summary. It is not a suggestion. It is not an answer to the question asked.)*

> **Q: how does your vision develop?** *(on the `converse` path)*
> **A:** noted

**A REGRESSION this grounding introduced, reported rather than hidden.** Before grounding,
`converse` answered this with the honest floor *"I can't say precisely how I vision."*
After grounding it answers **"noted"** — a bare acknowledgment, which is *less* honest.
Cause, traced: with no held `SelfProcess`, `comprehend_text` routes the question to
`path="honest_self"` and `converse` renders the floor. With one held, it routes to
`path="meta", meta_target="self_process"` — and `converse`'s read-off precedence has no leg
that renders `comprehend_text`'s meta dispatch, so it falls through to leg 4, the mechanical
minimal ack. `answer_question` **does** render it (see above). So `answer_question` and
`converse` diverge on the same question, and holding the true account makes the chat path
worse. One seam, precisely located.

### The gap spine — this part genuinely fires

The gaps below were filed **by the agent's own rules**, in its own `run_rules` fixpoint,
during the questioning. Nobody filed them.

> **Q: what gaps do you have?**
> **A:** I currently hold 5 gaps I've flagged about myself (4 implicit, 1 explicitly reported): (1) “direction selectivity” (self_account); (2) “vision retractions” (knowledge); (3) “convergence” (knowledge); (4) “orientation” (knowledge); (5) “you cannot develop direction selectivity” (reported).

> **Q: you cannot develop direction selectivity**
> **A:** Noted -- I've filed that as a gap to work on. I won't change myself without review.

Read gap (1) carefully. **`direction selectivity` (self_account)** — the agent understood
that "how should you fix your direction selectivity?" was a question about *its own
faculty*, found it held no account of how to fix it, and filed a self-account gap about
itself. That is `note_self_account_gap` doing exactly what CLAUDE.md's "THE AGENT FINDS ITS
OWN GAPS" section says it does, on vision, for the first time. It is also the single most
useful thing in this transcript, and it is a *pointer to* a gap, not a thought about one.

Gaps (2)(3)(4) are **diagnostic of my grounding, not of the agent**: I filed HeldAnswers
under topics `the vision retractions` / `learning rule convergence` / `orientation map`,
and its topic extractor keys on `vision retractions` / `convergence` / `orientation`. The
keys missed, so it honestly reported not holding them **and filed a gap for each**. The
gap-filing machinery is working; my topic keys were wrong. Note also that the baseline's
“vision” gap is *gone* after grounding — that one self-healed.

`induce_concern` — the `sd_*` loop — **does** engage when the finding is handed to it as a
relation-system:

```
rf.induce_concern(a, [["attractor","oja","time_averaged_covariance"],
                      ["direction","motion","isotropic_on_average"],
                      ["selectivity","direction","absent"]])
→ {'minted': True, 'capability_key': 'vision_direction_selectivity',
   'residual_predicates': ['attractor', 'direction', 'selectivity'],
   'closest_held_shape': 'T',
   'note': 'no held term-shape covers the observation; minted an induced
            CapabilityAxis from the residual structure'}
```

But *I* built that triple set by hand from the prose. Nothing in the agent reads its own
`HeldAnswer` text and produces the relation-system — so this is the loop working on an
observation a human decomposed for it, which is precisely the thing the vision arc's open
charge is about.

The NL promote path did not fire in-process: **"work on the direction selectivity gap"** →
**"noted"** (the steering rule marks `promote_requested`, and the *daemon's* `_steer_tick`
executes the human-gated promote — no daemon here, so no promotion). And:

> **Q: what experiments are you running?**
> **A:** I am working on 2 promoted concerns: (1) “standing_motor_intent” (pending); (2) “standing_self_improvement” (pending).

Neither is about vision. **Grounding the science produced no vision experiment, no vision
`StandingConcern`, and no proposal.**

---

## VERDICT — did the bet pay?

**Partly, and the honest reading is not flattering.**

**It paid on inspection and on gap-finding.** The science went in through the ordinary
`teach()` facility as ordinary graph data, in types the machinery already reads, with no
Rust and no new Python decision logic. The agent then answered from it, in first person,
routed by its own seed rules — *including reciting the charge that its own vision is a
connectionist model it is merely hosting*. And its gap spine fired on vision without being
asked to: it filed a **self_account** gap on direction selectivity, filed knowledge gaps
that correctly diagnosed my own bad topic keys, accepted an explicit deficiency report, and
refused to act on any of it without human review. That is the architecture behaving as
designed.

**It did not pay on reasoning, which is what the task was actually asking.** The agent has,
in one graph: the fact that Oja's attractor is the leading PC of a time-averaged
covariance; the fact that the average has no direction; the fact that its rung-3 nulls
follow from those two; the named next hypothesis (an attractor that is not the average,
symmetry-breaking faster than the averaging timescale); the standing rule that this needs a
new pre-registration and not a parameter sweep; and a `sd_*` loop that mints capability
axes from residuals. **It composed none of them.** Asked why its direction selectivity
fails, it explained NSFW. Asked how to fix it, it said "I can't say precisely how I
direction selectivity." Asked what to try next, it re-served a paragraph it had been
handed. There is no faculty that reads a held answer and *derives* anything, and the one
loop that could — `induce_concern` — only accepts a relation-system a human decomposed.

**Zero usable suggestions were produced.** The one thing it contributed to the vision work
is the pointer "direction selectivity (self_account)" — it knows it doesn't know. That is
worth something and it is not a research suggestion.

**So: the bet's premise is intact and its payoff is unclaimed.** The claim "every decision
is inspectable graph data the agent could edit" is TRUE of the retrieval and gap layers and
was demonstrated here for the first time on vision. The claim it is *meant* to cash —
that graph-residence buys the agent the ability to reason over and modify its own
faculties — is **not demonstrated, and this run is evidence against assuming it follows.**
Grounding was necessary and it was not sufficient. Vision's own open charge ("hosted, not
forcing the paradigm") now has a companion: **the agent's self-knowledge is stored, not
thought with.** The two are the same shape of finding, one level up, and neither is closed
by anything in this commit.

---

## Reproduce

```bash
python scripts/ground_vision_science.py      # idempotent; writes seeds/vision_science.json
```

Then, in a booted `WorldAdapter`, call `ground(agent)` (which re-wires the
`agent -holds_answer->` edges the seed format cannot carry) and `converse(...)`.

Gate: `pytest tests/ -k vision -q` — **10 failed, 118 passed, byte-identical with and
without `seeds/vision_science.json`** (verified by removing it and re-running): the 10 are a
pre-existing baseline from the concurrent rung-3/rung-5 work, and this commit is
gate-neutral. Additive only;
no `seeds/vision_*.json`, `domains/wave_world.py`, `domains/cortex_sheet.py`, or
`VISION_RUNG*_PREREG.md` touched).
