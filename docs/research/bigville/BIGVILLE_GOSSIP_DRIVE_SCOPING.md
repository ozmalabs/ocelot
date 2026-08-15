# BIGVILLE — THE MISSING GOSSIP DRIVE: A CAPABILITY-GAP SCOPING

Status: SCOPING ONLY. No seed, world, script, or test file was written or
modified to produce this document. No engine touched. No test run.

**REPO-LOCATION CORRECTION (2026-08-15, added after the original audit).**
This doc's Part 1 audit was originally run against Ocelot's own then-current
copy of the Bigville implementation. **The canonical Bigville implementation
has since been extracted into its own repository**, `ozmalabs/bigville`,
cloned locally at `/home/matt/ozmadev/bigville` (Ocelot's own
`worlds/bigville_world.py`, `domains/bigville_entities.py`, and
`seeds/bigville_*.json` are now gone — commit `5065fb8`, "Extract Bigville
implementation from Ocelot"; this line's own `docs/research/bigville/*.md`
research docs, including this one, were NOT part of that extraction and
remain here). **Every specific claim in Part 1 below was re-verified
directly against the real, separate `bigville` repo** (not re-derived from
memory) and **every one held exactly as originally written** — the `share`
branch's hardcoded weather placeholder, `bond_gossip_update`'s absence from
the live actor's loaded seed manifest, `hear_gossip`'s single call site
(only from `tests/test_bigville_bond_migrated.py`), and the Python `max()`
event-selection residual are all still true, verbatim, in the real repo.
One thing did move: `web/townview/server/app.py` no longer exists under
that name — its live-visualisation role is now `bigville/server.py`
(`GameService`, built on `bigville.api.create_game`), confirmed to serve the
same purpose. **Below, every file path is relative to
`/home/matt/ozmadev/bigville`, NOT to this Ocelot repo** — and any future
BUILD of Part 3's design must happen in that repo, not this one.

**BUILD LANDED (2026-08-15, `ozmalabs/bigville` commit `714d0fe`) — WITH ONE
LOAD-BEARING CORRECTION TO PART 3's OWN DESIGN.** Before building, direct
reading of `bigville/runtime.py::BigvilleGraph` found it has **no
rule-evaluation engine at all** — `load_seed_manifest` only stores manifest
data; nothing walks a seed's `Argmax`/`Term` tree and executes it. This
standalone repo does not depend on Ocelot's Rust `substrate_rs` DSL
evaluator. **The decision logic Part 1 read as a declarative Argmax
(`sp_choose_utterance`) is, in the live code, a hand-written Python
if/elif chain (`decide_speech`) that computes the same formula by hand** —
the seed JSON is closer to documentation/spec than executable rule data in
this repo. Consequently Part 3's own "load the `bigville_bond_update` seed
manifest into the live actor's mind so `bond_gossip_update` runs" plan was
**not buildable as written** — there is no engine to run it. The build
instead ported `hear_gossip`'s tested formula
(`content_valence * gossip_weight * source_trust`) directly into a new
Python method (`_hear_gossip`) on the live `BigvilleWorld`, exactly mirroring
how `decide_speech` already hand-implements `sp_choose_utterance`. A THIRD
gap, more fundamental than either of Part 1's two, was also found only by
building: `_spontaneous_speech_tick`'s single call to `decide_speech` never
passed `share_salience` at all, leaving it at its `0.0` default — `share`
was structurally unreachable in the live path regardless of the other two
fixes. All three are now closed (`_speech_share_event` computes real
salience from `observed_event` data; `_speech_goal`'s `share` branch renders
the real event; `_hear_gossip` moves the listener's belief, gated correctly
on trust in the source). Verified end-to-end in a live simulated town, not
just unit-isolated. 9 new tests + the repo's existing 152, all green. Full
detail: `ozmalabs/bigville` commit `714d0fe`'s own message.

This is a capability-gap analysis, not a harm-induction rung — it does not
carry (and does not need) the abuse line's Part D ethics protocol. The
question is whether Bigville residents have a *reason* to tell each other
things, not whether telling causes harm.

## THE CLAIM UNDER TEST, STATED PRECISELY

The user's framing: *"The agents have the ability to talk, and the
information, but not the inclination. They have a bond system but are
missing a drive to form those bonds."* Unpacked into checkable parts:

1. Agents CAN talk (a mechanical speech capability exists).
2. Agents HAVE information (things observed/known, representable in the
   graph).
3. Agents HAVE a bond/relationship representation.
4. Agents LACK a DRIVE — a motivated push to spontaneously share (3) using
   (1) about (2), especially as a bond-building act, not just an information
   transfer.

Part 1 below tests all four independently against the actual code. The
headline result, stated now so it isn't buried: **(1)-(3) are all true, and
(4) is TRUE BUT NOT IN THE SHAPE THE QUESTION ASSUMES.** A share-driven,
bond-weighted, information-gated Argmax choice already exists and is already
live in the canonical town simulation. What is actually missing is not the
drive itself but the two pieces of PLUMBING the drive's output depends on to
be recognisable as gossip: it currently fires into a content dead-end and a
listener dead-end. Part 1 documents this precisely; Part 3 designs the
minimal fix as a composition of already-built, already-tested atoms.

## SEARCH-AVAILABILITY NOTE — TESTED FIRST

WebSearch was invoked and returned live, dated, real results (verified via a
`Dunbar gossip 65% conversation time` query and a `Feinberg Willer Stellar
Keltner` query, both returning correct titles/venues/DOIs matched against
independent secondary confirmation). WebFetch against a live JASSS URL
(`jasss.org/26/4/1.html`) also succeeded and returned an accurate methods
quote. Search is live for this session; every citation below was checked
against real search results, not recalled from priors alone.

## CONFIDENCE-TIER LEGEND

- **HIGH** — peer-reviewed, well-cited, corroborated across independent
  sources or a canonical single source with wide subsequent citation.
- **MEDIUM** — a real, checkable single source, not independently
  cross-confirmed in this pass.
- **LOW** — real but thin (a widely repeated figure whose precise
  provenance is soft, or a single non-peer-reviewed source).
- **GAP-CONFIRMED** — searched for directly, and the search itself is the
  finding (nothing meeting the bar, or the closest match explicitly does
  NOT do what would be needed).

---

## PART 1 — THE CODEBASE AUDIT (read first; everything downstream depends on this)

### 1.1 — Speech mechanics: real, live, and already bond-aware

`seeds/bigville_speech_decide.json` (block 278000, `bigville_speech_decide`)
is a full EMERGENT speech-decision rung, not a scripted turn-taker. Its
headline rule `sp_choose_utterance` is an `Argmax` over a global
`SpeechOption` menu (`worlds/bigville_speech_world.py::SPEECH_MENU`) that
**includes `stay_silent`** as a candidate. The value function is:

```
value = occasion × relationship(Bond) × norm(pending FPP) × goal × affect_gain
        − face_cost − civil_inattention
```

evaluated per option, over a per-agent `loquacity_threshold`. This is
exactly the `Appraisal`+`Argmax` shape CLAUDE.md documents as the project's
standing drive template (the same family as `af_choose_action`,
`ss_choose_burn`, `mv_urge`). **One of the fifteen menu entries is `share`**
(`kind_code=5.0`, `confide_aff=1.0`, `base_value=0.2`, `face_cost=1.0`) whose
Argmax term (`bigville_speech_decide.json` lines ~448-518) is:

```
Times[ affect_gain, confide_aff, tie_strength, share_salience ]
```

— i.e. the `share` option's competitiveness is the PRODUCT of the bond's
`tie_strength` (read straight off the held `Bond(A→B)`) and `share_salience`
(a situational input, see 1.2). **This is already a bond-weighted,
information-gated push toward sharing.** It is not a label; it is a real
term in a real Argmax that a zeroed `confide_aff`/`tie_strength` coupling
would collapse (the seed's own stated falsifier).

This rung IS loaded into the canonical live-town class:
`worlds/bigville_world.py::BigvilleOcelotActor.__init__` calls
`self.inner.load_seed_manifest(manifest_for("bigville_speech_decide"), ...)`
and `bigville_loud_comm` (delivery/loudness), and `bigville_speech_world.py`
itself says explicitly: *"The canonical `BigvilleWorld` now reuses this same
seed-driven mechanism for resident encounters; this module remains the
small standalone proof harness."* `web/townview/server/app.py` drives
`worlds.bigville_world.BigvilleWorld.from_town100(...)` for the live
visualisation — confirmed by reading the endpoint. So: **agents CAN talk,
mechanically and live, and the choice to talk already reads a bond.**

### 1.2 — Information representation: real, and already feeding the share decision

An observed fact is an `Event` node (`worlds/bigville_world.py::create_event`,
line ~1202): `{kind, subject, detail, public, severity, day}`, linked to its
observer via an `observed_event` edge
(`self.eng.add_edge_unchecked(self._actors[observer], "observed_event", event)`).
This is the "things an agent knows" representation the user's framing
assumed exists — and it does.

`_speech_encounter_inputs` (line ~4582) computes `share_salience` FROM this
representation, not from a scripted schedule: it walks the speaker's
`observed_event` neighbours, and for any event ≤1 day old, takes
`max(0.25, severity)` as `share_salience`. **This is a real, non-trivial,
information-gated input** — a speaker with no recent salient event
contributes `share_salience=0.0` and the `share` option loses its
competitive edge in the Argmax. Section 1.4 names the one honest
architecture-rule residual in this step (the winning event is chosen by a
Python `max()`, not a graph Argmax).

### 1.3 — The bond system: real, general-purpose, and DISTINCT from the abuse line's traumatic-bond machinery — but its own update rules are not wired into the live town

`seeds/bigville_bond_update.json` (block 277000, `bigville_bond_update`) is
Bigville's own general per-agent, DIRECTED, subjective `Bond(A→B)` — three
dissociable slots (ToM belief decode, six signed relational emotions, one
signed attraction value) plus an earned `tie_strength`/`band`. It is a
SEPARATE system from the abuse research line's `harlow_attachment`/
traumatic-bond seeds (block ~283000): nothing in this file references
trauma, coercion, or the abuse-line's `stated≠held` credibility machinery. It
is exactly the "general social-relationship representation" the task asked
to confirm is not confused with the abuse-line's specific mechanism, and it
is not.

Seven rules compose it, and one is directly on-point:
**`bond_gossip_update`** ("INDIRECT third-party update ... C tells A about
B; A revises Bond(A→B) belief/affect/attraction by
`update_gain*content_valence*source_trust*gossip_weight` — WITHOUT A
directly experiencing B ... gossip is EVIDENCE WEIGHTED BY THE SOURCE, never
ground truth"). This is REAL, BUILT, and TESTED
(`tests/test_bigville_bond_migrated.py`). The mint side is
`worlds/bigville_bond_world.py::BigvilleBondWorld.hear_gossip(a_name,
about_b, from_c, content_valence)` — a clean, mechanical world-adapter
method that reads `source_trust` off `Bond(A→C)`, mints a `Gossip` node, and
attaches it via `has_gossip` for the rule to consume.

**The gap, precisely:** `hear_gossip` is called from EXACTLY ONE place in
the whole repository — `tests/test_bigville_bond_migrated.py`. It is never
called from `worlds/bigville_world.py`. More importantly, **the entire
`bigville_bond_update` seed manifest (all seven rules, including
`bond_gossip_update`) is never loaded into `BigvilleOcelotActor`'s mind
graph.** `BigvilleWorld` imports only `BOND_KNOBS`/`SLOT_DEFAULTS` (a plain
dict of default attribute values) from `bigville_bond_world.py` — it uses
`Bond` nodes as passive attribute carriers (`_speech_bond`, line 91, sets
`tie_strength`/`affect_affection`/`affect_resentment` directly from a
Python-side `_relationships` dict) but never runs the RULES that would let a
bond update itself from a benefit, a betrayal, a similarity signal, or a
piece of gossip. In the live town, a `Bond` is a static value bag, not a
dynamical object — the dynamics rung (block 277000) is fully built and
fully tested, but only in its own standalone `BigvilleBondWorld` harness,
never in the town residents actually live in.

### 1.4 — Where the drive's output currently goes: two dead ends, both mechanical, both fixable without new decisions

Given 1.1-1.3, the Argmax genuinely can and does select `share` in the live
town. Two things happen next, and both are gaps:

**(a) Content is generic, not the actual event.** `_speech_goal` (line
~4513), for `kind == "share"`, returns a HARD-CODED meaning:
`{"news": {"of": {"village": {"weather": weather}}}}` — regardless of which
`Event` actually drove `share_salience` above zero. The winning event's
`kind`/`subject`/`detail` (a real graph fact — who did what) is computed in
`_speech_encounter_inputs` only as a scalar severity, then discarded; it
never reaches `_speech_goal`. **The agent's Argmax genuinely decides "I
should tell this person something," reading a real fact, but by the time
speech is rendered, WHAT gets said has been silently replaced with
weather.** This is a content-plumbing gap, not a decision gap.

**(b) There is no listener uptake at all.** `_spontaneous_speech_tick`
(line ~4633) records `heard: bool(...)` on the resulting `Utterance` and
appends a `_speech_events` log entry, but nothing reads a heard `share`
utterance and mints a `Gossip` node on the LISTENER's own
`Bond(listener→subject)`, nor propagates `observed_event` to the listener
(so they could re-share later — second-hand spread). The exact mechanism
that would close this loop (`bond_gossip_update` + `hear_gossip`'s minting
pattern) already exists, tested, per 1.3 — it is simply never invoked from
the live town's speech tick.

**Net effect: even when the drive fires correctly (a real bond-weighted,
information-gated Argmax choice to `share`), no actual gossip — a specific
fact about a specific third party, transmitted and believed with source
discount, updating the listener's own social model — occurs. What is
observably emitted is an untethered "the weather is nice" utterance, and
nothing changes in the listener's graph.** This is a materially different
(and more precise) diagnosis than "no inclination exists": the inclination
exists and is already in the CLAUDE.md-preferred Appraisal+Argmax shape; the
two mechanical bridges downstream of it are missing.

**Honest residual, named but out of scope for this design:** the selection
of WHICH observed event drives `share_salience` is currently a Python
`max()` over `observed_event` neighbours in `_speech_encounter_inputs` — an
`if`/comparison over graph state deciding a value, which is exactly the
architecture-rule violation CLAUDE.md's self-correction prompts describe.
It predates this scoping and is not part of the user's gossip-drive ask, but
a correct wiring of the content bridge in Part 3 would naturally replace it
with an `Argmax` rule (the same `bond_belief_infer`-style
Argmax-by-fit pattern already used in `bigville_bond_update.json`) rather
than propagate the existing Python decision further.

### 1.5 — The generic Drive/motivation engine exists, is the right shape, and is ALSO unwired from the live town

`seeds/bigville_motivation.json` (block 325000, "cognitive C1") is a fully
general `Drive{kind, level, setpoint, weight}` node type with
`mv_urge`/`mv_arousal`/`mv_bootstrap`/`mv_switch` — urge = deficit × care
weight, arousal = max urge, and Argmax-with-hysteresis pursuit exactly
matching the em_happiness/`Argmax`-over-`Appraisal` template CLAUDE.md
names as the project's standing drive shape. Its own description text names
a data-driven drive set of "sustenance + competence/affiliation/certainty."
`seeds/bigville_need_drive_goal.json` (block 250000) is the companion
"a drive above threshold mints a spatial GOAL" rung —
`nd_arbitrate`/`nd_form_sustenance_goal`/`nd_form_rest_goal` — the exact
template a `ShareGossipGoal` would extend (see Part 3).

**Both are confirmed, by grep, to be loaded nowhere in
`worlds/bigville_world.py`** — they exist only in their own standalone
`worlds/bigville_motivation_world.py` / `worlds/bigville_need_world.py` test
harnesses (`tests/test_motivation_migrated.py`,
`tests/test_bigville_need_migrated.py`). **"Affiliation" is named only in
the block-325000 seed's prose description; no code anywhere instantiates an
`affiliation` (or any bonding-flavoured) `Drive` node for any agent.** This
is an important negative finding for Part 3: the obvious-looking answer
("just add a `Drive{kind:'affiliation'}` and let the existing engine mint a
goal") would require wiring an entire currently-standalone rung into the
live town, which is a larger and separately-scoped piece of integration
work than the two dead-end fixes in 1.4, and is not needed for a minimal
first design because 1.1 already shows a working Appraisal+Argmax drive
firing at the right decision point.

### 1.6 — Other gossip-adjacent machinery, checked and correctly characterised

- **`seeds/bigville_loop_reputation.json`** (block 253000):
  `bl_badmouth`/`bl_townsfolk_opinion` — a creditor badmouths a defaulting
  debtor; townsfolk opinion flips via a standing-vs-testimony comparison.
  Re-read for THIS purpose per the task's instruction: it is a real,
  working belief-propagation mechanism, but it is scoped to the
  economy→affect→society hop specifically (debtor default), and — like
  1.3/1.5 — it is not loaded into `BigvilleWorld` either (same grep-confirmed
  absence). It is not the general "tell someone something" mechanism; it is
  a narrower, economy-triggered instance of the same shape.
- **`seeds/bigville_drama_social.json`** (block 245000): `bd_mary_infers`
  (ToM belief decode, generalised by `bond_belief_infer` above),
  `bd_villager_backs` (standing-vs-testimony credibility), `bd_john_public_face`
  — this is the main-cast (John/Mary) political-drama rung, also not loaded
  into the general-population `BigvilleWorld`. It is the historical source
  the general `bond_belief_infer`/`bond_gossip_update` rules in block 277000
  were explicitly written to GENERALISE, per that seed's own description
  ("generalizes bd_mary_infers to any A about any known B" /
  "generalizes bl_badmouth"). Block 277000 is therefore already the correct,
  intended successor mechanism — it just isn't wired in yet (1.3).
- **The `bigville/` directory** (`game.py`, `character.py`, `api.py`,
  `backends/`) is a turn-driven, human/LLM-backend playable session layer
  BUILT ON TOP OF the same canonical `BigvilleWorld`
  (`bigville/api.py` imports `worlds.bigville_world.BigvilleWorld`) — not a
  separate simulation. It adds conversation backends (a template interface,
  a "cheap" backend, an Ocelot backend, a human backend) for actually
  rendering free text, but does not change any of the findings above.
- **A concrete illustration the audit turned up unprompted:**
  `seeds/bigville_townspeople_50.json` names a resident, "Hepzibah Vole",
  with `"role": "gossip"` — but the role is flavour text only
  (`"motivation": "An ordinary resident of Bigville."`); nothing in the
  mechanics gives this named archetype any distinct `confide_aff`,
  `loquacity_threshold`, or bond-update behaviour. The town already has a
  character written for this role and no mechanism that makes her live up
  to it.

### 1.7 — Part 1 summary table

| User's claim | Verified? | Precise finding |
|---|---|---|
| Agents can talk | YES | `bigville_speech_decide` (278000), live in canonical `BigvilleWorld`, Argmax over 15 options incl. `stay_silent` |
| Agents have information | YES | `Event`/`observed_event` graph representation, real, feeds `share_salience` |
| Agents have a bond system | YES, but static in the live town | `Bond(A→B)` node (277000 schema) held and read by speech decide; its OWN update rules (belief/event/gossip/similarity/proximity) are not loaded into the live town — bonds don't move on their own there |
| Agents lack a drive to share | PARTIALLY TRUE, PARTIALLY FALSE | A real bond-weighted, information-gated Argmax push toward `share` already exists and already fires live. What's actually missing is (a) the content bridge (real event → rendered utterance) and (b) the listener-uptake bridge (heard share → listener's own Bond/Gossip update) — both mechanical, both composable from already-built, already-tested atoms (1.3/1.4) |

---

## PART 2 — THE LITERATURE, GROUNDED

### 2.1 — Gossip as social grooming / bonding, not (only) information transfer — [HIGH]

Dunbar, R.I.M. (1996). *Grooming, Gossip, and the Evolution of Language*.
Harvard University Press. Dunbar, R.I.M. (2004). "Gossip in Evolutionary
Perspective." *Review of General Psychology*, 8(2), 100-110. The
social-brain-hypothesis argument: primates maintain coalitions via physical
grooming, which does not scale to human group sizes (~150, "Dunbar's
number"); language, and specifically gossip, is proposed as the scalable
substitute — cheaper per-bond maintenance, sustaining many more relationships
in parallel. The commonly-quoted **"gossip is ~65% of conversation time"**
figure traces to Dunbar's own conversation-sampling studies and is widely
repeated; the precise percentage is a field-observation estimate (not a
single controlled experiment), so treat the number itself as **LOW-tier
precision** while the qualitative claim (gossip/social-topic talk dominates
ordinary conversation time) is HIGH-tier and multiply corroborated.

### 2.2 — Gossip has a taxonomy of motives, and "relationship building" (bonding) is one of them, DISTINCT from information-seeking — [HIGH]

Foster, E.K. (2004). "Research on Gossip: Taxonomy, Methods, and Future
Directions." *Review of General Psychology*, 8(2), 78-99. Names four
functions: information (tracking social networks), friendship (strengthening
bonds), influence (impression management), entertainment.

Dores Cruz, T.D., Nieper, A.S., Testori, M., Martinescu, E., & Beersma, B.
(2021). "An Integrative Definition and Framework to Study Gossip." *Group &
Organization Management*, 46(2), 252-285. A later, empirically-validated
six-motive model: information validation, information gathering,
relationship building, protection, social enjoyment, negative influence —
with information-related motives most prevalent, but relationship-building
(bonding) confirmed as a **distinct, measured motive independent of the
informational content's truth value or novelty**. This is the precise
literature-side confirmation of the user's own framing: "a drive to FORM
BONDS," not merely a channel that moves facts. The RGFQ follow-up
(Hogrefe, *Psychological Test Adaptation and Development*, 2024/2025) is
the psychometric instrument built on this framework.

### 2.3 — Gossip as reputation-based, prosocial cooperation-sustaining behaviour — [HIGH]

Feinberg, M., Willer, R., Stellar, J., & Keltner, D. (2012). "The Virtues of
Gossip: Reputational Information Sharing as Prosocial Behavior." *Journal
of Personality and Social Psychology*, 102(5), 1015-1030. Establishes
"prosocial gossip" — sharing negative evaluative information about a
transgressor to protect a vulnerable third party — as motivated by
prosocial concern (not malice), and shown to repair the gossiper's own
negative affect. Feinberg, M., Willer, R., & Schultz, M. (2014). "Gossip
and Ostracism Promote Cooperation in Groups." *Psychological Science*.
Extends the mechanism to group-level cooperation maintenance.

Nowak, M.A., & Sigmund, K. (1998). "Evolution of Indirect Reciprocity by
Image Scoring." *Nature*, 393, 573-577. The foundational formal model:
cooperation with strangers is sustained not by direct reciprocity but by
observers building and propagating a reputation ("image score") of an
individual's past cooperativeness — gossip is the transmission channel a
reputation economy needs to function beyond the observer's own direct
witness.

### 2.4 — A salient (emotionally significant) event is disproportionately likely to be shared, and shared SOON — [HIGH, and directly on point for the codebase's own `share_salience` design]

Rimé, B. (2009). "Emotion Elicits the Social Sharing of Emotion: Theory and
Empirical Review." *Emotion Review*, 1(1), 60-85. Across eight independent
recall studies (1,384 emotional episodes, 913 respondents), **88-96% of
emotionally significant experiences are shared with someone**, and the modal
pattern is same-day sharing (≈60% of first-sharing events occur the day of
the episode). **This is worth flagging as a genuinely notable finding of
this audit**: `_speech_encounter_inputs`'s existing `share_salience`
computation — `age ≤ 1.0 day` gating a `severity`-weighted salience — already
encodes Rimé's same-day-sharing finding, and the seed file's own inline
comment (`"share_salience ... an emotionally-salient event to share
(Rime)"`) shows the original implementer already had this citation in mind.
The mechanism this scoping is being asked to complete was already grounded
in the correct literature at the point it was half-built; the missing half
(content + listener bridges) was simply never finished.

### 2.5 — Is "the decision to gossip, as a motivated act" well-trodden ground in computational/ABM modelling, or a genuine gap? — [GAP-CONFIRMED]

Testori, M., Giardini, F., Dores Cruz, T.D., & Beersma, B. (2023). "What
Matters Most in Supporting Cooperation, the Gossip Content or the
Gossiper's Intention? Simulating Motive Interpretation in Gossip Dynamics."
*Journal of Artificial Societies and Social Simulation*, 26(4).
DOI: 10.18564/jasss.5194. This is the closest computational precedent found
(and the JASSS "gossip ABM" literature broadly). Fetched and read directly:
**gossip-sharing in this model is exogenous and mandatory, not motivated** —
its own methods text: *"each agent shares x gossip statements (default:
x=2) about their most recent interaction partners with their current
interaction partner"*, every round, unconditionally. Agents are assigned a
fixed gossip MOTIVE label at initialisation (used only to interpret/react to
gossip they RECEIVE), but nothing in the model computes WHETHER to gossip
from a drive, goal, or bond state — only WHAT is said (content) and how it
is INTERPRETED varies.

**This is the honest answer to the task's Part 2 question:** the ABM
literature studies gossip's CONTENT dynamics and reputation-propagation
consequences extensively (the reputation/image-scoring line, 2.3, and its
many JASSS-hosted extensions), but modelling **the decision to gossip as
arising from a motivated computation** (a drive/goal/bond-weighted choice,
rather than a scheduled or forced event) does not appear to be
well-trodden ground — at minimum, the closest and most recent purpose-built
gossip ABM found explicitly does the opposite. Bigville's own
`sp_choose_utterance` Argmax (1.1) is, by this comparison, already ahead of
the closest published computational precedent on exactly the dimension this
scoping was asked to investigate — it just isn't finished. This should be
read as a genuine but narrow gap-confirmation (one search pass, one
close-fit paper fetched and verified in detail), not an exhaustive
literature review.

---

## PART 3 — THE PROPOSED DESIGN (mechanism, not labels; reuse, don't invent)

### 3.1 — What NOT to build, and why (given Part 1's actual findings)

A first instinct — "add a `Drive{kind:'affiliation'}` node and let the
block-325000 motivation engine mint a `ShareGossipGoal`" — is the wrong
minimal move. Per 1.5, that entire engine (both `bigville_motivation` and
`bigville_need_drive_goal`) is itself unwired from the live town; adopting
it as the vehicle for this fix would mean standing up an entire second,
currently-standalone cognition rung as a prerequisite, which is a
disproportionate amount of new integration surface for what Part 1 shows is
actually a two-bridge plumbing problem. It is named below (3.4) as the
correct SECOND rung, not the first.

A second wrong instinct — inventing a brand-new "gossip drive" scalar (a
`gossip_urge` knob, a new node type, a bespoke rate) — is exactly the
pattern CLAUDE.md's "SHAPES, NOT NUMBERS" section names as the standing
failure mode: a new subsystem reaching for a scalar knob instead of asking
whether the shape already exists. Per 1.1, it already does: `sp_choose_utterance`
is already the Appraisal+Argmax drive, already reads a real bond and real
information, already fires in the live town. Inventing a second, parallel
drive mechanism next to it would be exactly the "each ad hoc rate eventually
needs its own rate" regress the F-16/humanoid retrospectives diagnosed.

### 3.2 — The minimal first design: close the two bridges, invent nothing new that isn't strictly required

**Bridge (a) — content.** The winning `Event` that produces `share_salience`
must reach `_speech_goal`'s `share` branch instead of being discarded as a
scalar. Concretely: `_speech_encounter_inputs` currently computes
`share_salience` via a Python `max()` over `observed_event` neighbours
(1.4's named residual) — the correct fix moves this selection into a graph
rule (an `Argmax` over `Neighbours(actor, "observed_event")` scored by a
recency-decay × severity term, composing `Attr`/`Minus`/`Abs`/`Times`
exactly as `bond_belief_infer`'s Argmax-by-fit already does in block
277000 — no new Rust, no new Term). The winning event's `subject`/`kind`/
`detail` then becomes the mechanical content of the `share` meaning
(`_speech_goal`'s `share` branch reads the SAME held Event the rule
selected, instead of `weather`). This is pure world-adapter translation
(mechanical: graph fact → rendered meaning), the same category of work
`_speech_goal`'s other eleven branches already do.

**Bridge (b) — listener uptake.** When a `share` `Utterance` is `heard=1`
(the flag already exists), the mechanical adapter step mints a `Gossip` node
on the LISTENER's own `Bond(listener→subject)` — reusing
`BigvilleBondWorld.hear_gossip`'s exact pattern (`from_c=speaker,
about_b=event.subject, content_valence=signed(event.severity)`,
`source_trust` read off `Bond(listener→speaker).belief_trust`) — and this
requires **loading the already-built, already-tested `bigville_bond_update`
seed manifest into `BigvilleOcelotActor`'s mind** (currently only its
default-attribute dict is imported, per 1.3) so `bond_gossip_update` and the
other six bond dynamics rules actually run for the residents who live in
the town, not only in the standalone `BigvilleBondWorld` harness. **Zero new
rules are needed for this bridge — `bond_gossip_update` already exists and
is already tested; the only change is wiring (load the seed) plus one
mechanical adapter call (mint the `Gossip` node on `heard`, mirroring
`hear_gossip`).**

### 3.3 — What's genuinely new vs. what composes existing atoms

| Component | Status |
|---|---|
| The drive (bond-weighted, information-gated Argmax choice to `share`) | EXISTING, already live (`sp_choose_utterance`, 278000) — reuse as-is |
| The listener-side belief/affect update mechanism | EXISTING, tested (`bond_gossip_update`, 277000) — reuse as-is |
| The mint-on-hearing pattern | EXISTING (`BigvilleBondWorld.hear_gossip`) — replicate the pattern, don't reinvent it |
| Loading `bigville_bond_update` into the live actor's mind | WIRING CHANGE — one new `load_seed_manifest` call, no new seed data |
| Content bridge: winning event → rendered `share` meaning | NEW mechanical adapter translation (a few lines in `_speech_goal`/`_speech_slots`) |
| Which-event-wins as a graph Argmax (replacing the Python `max()`) | NEW, one small rule composing existing Terms (Argmax/Attr/Minus/Abs/Times) — arguably a pre-existing architecture-rule debt this design pays down as a side effect, not new gossip-specific logic |
| Listener uptake hook: on `heard` share, mint `Gossip` on listener's Bond | NEW mechanical adapter hook (a few lines in `_spontaneous_speech_tick`), calling the existing pattern |
| New Drive node type / new scalar "gossip urge" knob | NOT PROPOSED — the shape already exists (3.1) |

The genuinely new surface is small and entirely composition-shaped: one
seed-load wiring change, one small graph rule that fixes a pre-existing
architecture-rule residual as a side effect, and two mechanical adapter
translations. No new Rust, no new node type, no new drive mechanism.

### 3.4 — Named, not built: the natural second rung (out of scope here)

If the minimal design (3.2) is built and the drive still under-fires because
agents only gossip when co-located BY CHANCE (the current
`_spontaneous_speech_tick` pairs residents opportunistically by shared
map cell — 1.1's Argmax never causes an agent to seek out a specific
confidant), the correct next move is to promote a held `share_salience` +
best-bond-tie-strength combination into a `ShareGossipGoal` via the
block-250000 `nd_form_*_goal` pattern (a drive above threshold mints a
spatial goal, exactly like `nd_form_sustenance_goal`/`nd_form_rest_goal`),
routed through the existing spatial-goal-seeking machinery. This would give
Dunbar/Foster's full "actively seeks out a confidant to share bonding-salient
news" behaviour, not just "shares if the confidant happens to be standing
there." It requires wiring the currently-standalone block-325000/250000
motivation engine into the live town (1.5), which is a materially larger
integration than 3.2 and is explicitly deferred, not designed here.

Also named, not designed: connecting a shared/spread belief to the abuse
line's `stated≠held`/credibility machinery (block 234000/245000) for what
happens when gossip is FALSE or weaponised — the task explicitly flags this
as likely out of scope for a first minimal design, and Part 1 confirms
`bond_gossip_update` already treats gossip content as "evidence weighted by
the source, never ground truth" (i.e. it already has an honesty/reliability
discount built in at the receiving end), so a first design does not need to
model deliberate deception to be coherent — it can start from gossip content
being a true report of a real `Event`, exactly matching prosocial-gossip
literature's dominant framing (2.3).

### 3.5 — The falsifiable prediction

With bridges (a) and (b) built: **given the SAME novel third-party `Event`
observed by two speakers with a shared co-location opportunity, the speaker
holding the STRONGER `tie_strength` toward the present interlocutor should
show a measurably higher rate of `share`-kind utterances AND — critically,
the part the current mechanism cannot produce at all — the listener's own
`Bond(listener→event.subject)` should show a measurably higher rate of
`Gossip`-driven belief/affect updates than a weakly-bonded pair given
identical information.** Zeroing the existing falsifier knobs
(`confide_aff`, `tie_strength`'s coupling in `sp_choose_utterance`, or
`gossip_weight`/`update_gain` in `bond_gossip_update` — all already shipped
as knobs in the two seeds) should collapse this back to the CURRENT
baseline: `share` chosen roughly independent of bond strength, content
generic, and zero listener-side updates — mirroring this whole research
line's standing falsifier-knob discipline.

---

## PART 4 — RETELLING DECAY (the user's own follow-up: dedup is not binary)

Once the two/three bridges above landed (see the BUILD LANDED note), the
next honest residual it surfaced was: nothing stops a speaker re-telling the
SAME news to the SAME listener every tick it stays salient and co-located.
The user's own framing sharpened the fix precisely: *"how do people dedupe
things? high salience gossip is often retold to the same person"* — i.e. a
naive "never repeat" rule would be WRONG, not just crude; real people retell
high-salience news to the same person, repeatedly, and stop only gradually.

**Grounded, search-verified (not recalled from priors), both real:**
- Clark, H.H. & Brennan, S.E. (1991), *"Grounding in Communication,"* in
  Resnick et al. (eds), *Perspectives on Socially Shared Cognition* (verified
  live). **Common ground is established PER-DYAD**, not globally — a speaker
  tracks what THIS listener already knows, not whether the news has been
  told to anyone. This is the reason dedup, if it exists, must be keyed on
  `(speaker, listener, event)`, never on the event alone: retelling a
  DIFFERENT person stays fully available even after five retellings to the
  first.
- Rimé, B. (2009), *"Emotion Elicits the Social Sharing of Emotion,"*
  **Emotion Review** (already grounded [HIGH] in Part A2.4 above, re-verified
  live for this specific claim). Direct finding: *"Social sharing is
  expected to be a repetitive phenomenon, declining over time... the best
  known predictor of the slope of this evolution [is] the initial intensity
  of the shared emotion."* More intense episodes are shared at ~90% within a
  week and DECLINE MORE SLOWLY, not less — i.e. high-salience news should be
  retold MORE before tapering, exactly the user's own observation, not an
  edge case to special-case away.

**The design, composing what already shipped:** not a binary "already told"
flag, but a per-`(listener, event)` retelling COUNT, held as a plain dict on
the actor mind (`BigvilleOcelotActor.told_events`, the same bookkeeping-dict
idiom `speech_bonds`/`speech_choices` already use — consistent with this
repo's own established pattern, not a new one), damping `share_salience`
multiplicatively PER LISTENER: `effective_salience = base_salience *
(retell_decay ** retell_count)`, where `retell_decay = min(0.95, 0.3 +
severity)` — a MORE severe event gets a decay rate CLOSER TO 1 (slower
decline, more sustained retellings), a mild event decays fast, matching
Rimé's own "initial intensity predicts the slope" finding directly rather
than by analogy. The count increments only when a `share` is actually heard
by that listener (mirroring the existing `_hear_gossip` call site exactly).
Reuses the SAME `value *= 1 - decay_rate`-shaped idiom this whole research
line has used repeatedly (R5's `r5_bond_extinguish`) — one new per-actor
dict, one new multiplicative term in the existing salience computation, zero
new node types, zero new rule mechanism.

**Falsifiable, not asserted:** with `retell_decay` forced to `0.0` (hard
one-and-done dedup), a high-severity event should show markedly FEWER total
retellings to the same listener than the real, severity-scaled decay rate
produces — the mechanism's whole point is that severity-scaled decay
produces MORE repetition for high-salience news, not less, which a
zero-decay control could not.

**BUILD LANDED (2026-08-15, `ozmalabs/bigville` commit `acf0961`).**
`BigvilleOcelotActor.told_events` (per-`(listener, event)` count, same
bookkeeping-dict idiom `speech_bonds`/`speech_choices` already use);
`_speech_share_event` now takes `listener` and damps each candidate event's
salience by `retell_decay ** count` before the max-selection, so a
still-being-retold event can still win against a fresher but milder one when
its damped salience remains highest; the count increments only on an
actually-heard share, at the existing `_hear_gossip` call site. Verified
live in a running town: an event told 11 times to one listener damped from
`0.6` to `~0.19` (retained, never zero); a never-told listener saw the full
undamped `0.6` in the same tick — confirming the per-dyad claim directly,
not just the decay curve. 4 new tests (13 total in the gossip suite) + the
repo's full 156, all green.

---

## OPEN QUESTIONS

1. **Does Bigville's speech mechanism carry arbitrary propositional
   content, or only a fixed vocabulary of scripted meaning-templates?**
   Confirmed: `_speech_goal` is a fixed Python dispatch over fifteen `kind`
   strings, each returning a hand-templated meaning dict; it is not a
   general natural-language generator. This determines the ceiling of the
   content bridge (3.2): it can carry the WHO/WHAT/SEVERITY of a specific
   `Event` (a straightforward templating extension), but it cannot yet
   render arbitrary free-form gossip content beyond that schema without
   separately extending `_speech_goal`'s vocabulary — genuinely uncertain
   whether that extension is trivial (more template branches) or requires
   touching the deeper `WorldAdapter` communicative-action faculty
   (`goal_utterance`, line 189) that actually renders and tracks addressee
   uptake.
2. **Should the content bridge render the event's `detail` string verbatim,
   or only its structured `kind`/`subject`/`severity`?** The `detail` field
   is free text (`create_event`'s `detail=""` parameter) and its provenance
   / who authored it is not audited in this scoping — verbatim quoting risks
   carrying content that was never validated as "sayable" by the speech
   vocabulary. Left open.
3. **How much of the second-rung goal-seeking design (3.4) is actually
   wanted before shipping 3.2?** If agents mostly stand still or move for
   independent reasons (harvest/trade/rest goals), 3.2 alone may produce
   very little observable gossip simply because co-location with a
   high-tie-strength target is rare. This is an empirical question the
   falsifiable prediction (3.5) would surface, not one this scoping can
   resolve without running the sim.
4. **Second-hand spread (gossip about gossip)** — 3.2's design has the
   listener update their OWN belief about the subject, but does not
   propagate `observed_event` (or a `Gossip`-derived belief) onward so the
   listener could later re-share it themselves. Whether that chain matters
   for a first design, or is itself the natural 3.4-adjacent extension, is
   open.
5. **The Rimé same-day-sharing citation (2.4) matches the existing
   `age ≤ 1.0` gate closely but not exactly** — Rimé's modal pattern is
   "same day" for ~60% of first sharings, not a hard cutoff; whether the
   existing `age <= 1.0` day threshold should be softened into a decayed
   weight (matching the literature's distribution more precisely) rather
   than a hard gate is a tuning question, not a structural one, and is not
   resolved here.

## BOTTOM LINE

The user's diagnosis is directionally right but the code shows something
more specific and, in one sense, better than assumed: Bigville is not
missing a gossip drive in the sense of missing motivational machinery — a
real, bond-weighted, information-gated Argmax choice to share already
exists and already runs live in the canonical town (`sp_choose_utterance`,
block 278000), grounded (per the code's own inline citation) in Rimé's
social-sharing-of-emotion literature. What is actually missing is two small,
already-solved-elsewhere bridges: the content of what gets shared is
currently discarded in favour of a weather placeholder, and nothing on the
listening end consumes a heard share into their own bond/belief state — even
though the exact listener-side mechanism (`bond_gossip_update`, block
277000) is already built and already tested, just never wired into the live
town. The literature (Dunbar's social-grooming account, Foster's/Dores
Cruz's relationship-building motive distinct from information-seeking,
Feinberg et al.'s prosocial-reputation account, and Rimé's salience/recency
finding already anticipated in the code) supports building exactly this:
gossip as a bond-serving act whose likelihood should scale with tie
strength independent of the information's novelty. The proposed minimal
design closes the two bridges by recomposing existing, tested atoms — no
new Rust, no new node type, and no new scalar drive — and names, but
explicitly defers, the larger (and separately-scoped) integration of
promoting this into an active confidant-seeking spatial goal.
