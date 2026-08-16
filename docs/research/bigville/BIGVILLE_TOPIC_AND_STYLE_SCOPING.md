# BIGVILLE — TOPIC DIVERSITY, PERSONAL EXPERIENCE, TALK RATE, AND STYLE: A CAPABILITY-GAP SCOPING

Status: SCOPING ONLY. No seed, world, script, or test file was written or
modified to produce this document. No engine touched. No test run.

**REPO LOCATION.** Per the same correction already recorded in
`BIGVILLE_GOSSIP_DRIVE_SCOPING.md`: the canonical Bigville implementation
lives in its own repository, `ozmalabs/bigville`, cloned locally at
`/home/matt/ozmadev/bigville` (a standalone game with its own README, no
CLAUDE.md, no dependency on Ocelot's Rust `substrate_rs`). **Every file path
and line number below is relative to `/home/matt/ozmadev/bigville`, verified
by direct reading on 2026-08-16, not carried over from the prior doc.** Any
future BUILD of Part 3's design happens in that repo, not this one.

This is a capability-gap analysis, not a harm-induction rung — no ethics
protocol needed. The question is what Bigville residents talk ABOUT, to WHOM,
how OFTEN, and in what REGISTER — not whether talking causes harm.

## THE CLAIM UNDER TEST, STATED PRECISELY

The user's framing: *"People talk about everything. Particularly salient
recent things, or things they did or learned recently, or their favourite
topics. People talk at different rates to strangers and friends etc, and
develop specific language/communication styles with close friends and
groups."* Unpacked into four independent, separately-checkable sub-claims,
per the task's own instruction not to conflate them:

1. **Topic diversity / idiolect.** The only non-generic speech content built
   so far is `share` (third-party gossip about an injury/death `Event`).
   Real conversation is dominated by the speaker's own recent salient
   experiences and by enduring individual topic preference (a smith talks
   about smithing more than a baker does) — closer to individual topic
   preference than to news-sharing.
2. **Personal-experience sharing, distinct from gossip.** First-person
   narrative about one's own actions/skill-learning/life events is a
   different speech act from third-party reporting, with different
   content-selection logic.
3. **Relationship-scaled talk RATE.** People initiate talk more often with
   friends than strangers — a measurable difference in HOW OFTEN a resident
   speaks at all, not just whether `share` is chosen.
4. **In-group / close-tie linguistic style convergence ("familect").** Close
   ties develop shared vocabulary/register outsiders don't use — a
   phenomenon about HOW something is said, distinct from RATE (3) and
   CONTENT (1-2).

Part 1 tests all four independently against the actual, current code. The
headline result, stated now so it is not buried: **all four are genuinely
absent as decision logic, but the codebase audit turns up a large amount of
already-built, already-tested plumbing each one can compose from — plus one
finding not previously flagged by the prior gossip scoping doc: the
population-scale relationship state that sub-claims 3 and 4 (and the
ALREADY-SHIPPED gossip mechanism from the prior doc) all depend on does not
exist for the general population in the live town today, at all.** Part 1.5
documents this precisely; it changes the shape of Part 3's design more than
any single literature finding does. **A second finding, surfaced mid-research
and load-bearing for Part 3's scope: sub-claim 4's real mechanism (a
personality-trait-quantized codebook) already exists, landed and measured —
but in Ocelot's own agent substrate, not bigville, and bigville's own
backend-boundary design (`bigville/backends/ocelot.py`) says it should stay
there.** This document therefore proposes THREE bigville-native rungs (topic
content, first-person experience, talk rate) and defers the fourth
(style/register convergence) to a named, pointed-at, out-of-repo build — see
1.9 and 3.4.

## SEARCH-AVAILABILITY NOTE — TESTED FIRST

WebSearch was invoked first against a real, checkable query (`Giles 1973
communication accommodation theory speech convergence divergence citation`)
and returned live, correctly-attributed results (Giles, Taylor & Bourhis
1973, *Language in Society* — matched against independent knowledge of the
citation). WebFetch against a live Cambridge Core URL and a live NCBI PMC URL
both succeeded and returned accurate content. Search is live for this
session; every citation below was checked against real search results (and
in three cases, fetched primary/secondary sources), not recalled from priors
alone.

## CONFIDENCE-TIER LEGEND

- **HIGH** — peer-reviewed, well-cited, corroborated across independent
  sources or a canonical single source with wide subsequent citation.
- **MEDIUM** — a real, checkable single source, not independently
  cross-confirmed in this pass.
- **LOW** — real but thin (a widely repeated claim whose precise provenance
  is soft, a single non-peer-reviewed source, or a secondary source standing
  in for an unfetched primary one).
- **GAP-CONFIRMED** — searched for directly, and the search itself is the
  finding (nothing meeting the bar, or the closest match explicitly does NOT
  do what would be needed).

---

## PART 1 — THE CODEBASE AUDIT (read first; everything downstream depends on this)

### 1.1 — Speech mechanics, re-verified: still a hand-written Python dispatch, not an executed rule engine

`worlds/bigville_speech_world.py::SPEECH_MENU` (lines 7-23) is confirmed
still 15 hardcoded `SpeechOption` dicts (`stay_silent`, `greeting`,
`smalltalk`, `barb`, `hedged`, `share`, `answer`, `request`, `offer`,
`question`, `thanks`, `apology`, `farewell`, `complaint`, `promise`), each
with `kind_code`/`talk_aff`/`base_value` (and a few with `confide_aff`,
`face_cost`, etc.). This file's own `decide()` method (lines 85-114) is the
small standalone proof-harness dispatch; the LIVE canonical path is a
separate, larger method.

**`worlds/bigville_world.py::BigvilleOcelotActor.decide_speech`** (class
`BigvilleOcelotActor` at line 33, method at lines 130-203) is confirmed to
still be a hand-written Python if/elif chain over the SAME 15-option
vocabulary (`SPEECH_KIND_LABEL`), computing by hand exactly the formula the
prior scoping doc found the seed JSON only *documents*: `sp_choose_utterance`
is not executed by anything in this repo (re-confirmed: `bigville/runtime.py`
has no rule-walking engine anywhere in its `WorldAdapter`/`BigvilleGraph`
classes). This is still true, verbatim, as of this audit.

### 1.2 — `role`/`trade`: a real, held, per-agent attribute, confirmed genuinely UNUSED for speech

`add_actor` (`worlds/bigville_world.py:4373-4421`) mints every resident as an
`Agent` node carrying `role` (a single string, e.g. `"smith"`), `trade`
(`next(iter(trades), role)`), `trades` (a comma-joined string of all trades),
plus `klass`/`group`, and an arbitrary `traits` dict merged directly onto the
node's attrs (this is how `scenarios/house_argument.json` sets a per-agent
`loquacity_threshold`, confirmed by grep). These are real, live, held graph
attributes — the exact "per-agent topic affinity" hook the user's framing
assumed exists.

**Grep-confirmed against the entire speech pipeline
(`_speech_bond`/`decide_speech`/`_speech_share_event`/`_hear_gossip`/
`_speech_goal`, lines 104-5555): zero references to `role` or `trade`
anywhere.** `tests/test_bigville_gossip_migrated.py`'s own test town
(`_town()`, lines 27-31) names its four residents "Anselm" (smith), "Bryony"
(collier), "Colm" (woodworker), "Dara" (baker) purely as narrative flavour —
nothing in the mechanics reads it. This is the SAME finding shape as the
prior doc's "Hepzibah Vole, role: gossip" residual (1.6 there): the town
already carries the exact per-agent signal this design needs, unconsumed.

### 1.3 — First-person self-experience events: representable by the EXISTING `create_event` shape, but not populated even for the two event kinds that already exist

`create_event(kind, *, subject="", detail="", observer=None, public=True,
severity=0.0)` (`worlds/bigville_world.py:2015-2024`) takes `subject` and
`observer` as fully independent parameters — nothing prevents
`subject == observer`, i.e. a resident as the subject of their OWN observed
event. This is genuinely, structurally sufficient for "things I did/learned
recently" with **zero new node types and zero new Rust** (this repo has none
to add to).

**But the finding is sharper than "unused, ready to use": grep confirms only
FOUR call sites for `create_event` exist in the whole repo** —
`weekly_village_report` (line 2105, `subject="Bigville"`, not a resident),
`injure` (line 4758, `subject=actor`), and `_record_death_event` (line 4849,
`subject=actor`). **Both `injure` and `_record_death_event` already set
`subject=actor` — the person it happened TO — but NEITHER passes
`observer=actor`.** `_record_death_event`'s own docstring says so explicitly:
*"Record a death as a world event without distributing knowledge."* The
separate, explicit `observe_event(observer, event)` method (line 2027) is the
only way to grant an `observed_event` edge after the fact — and grep confirms
it is called from exactly two files, both test files
(`tests/test_bigville_gossip_migrated.py`, `tests/test_ported_features.py`),
never from production code. **Consequence: today, a resident who is injured
does not automatically hold an `observed_event` edge to their own injury —
the "thing that happened to me" is a world fact the victim does not
mechanically know about, let alone can share.** This is a real, previously
unaudited gap one level below the one the task anticipated (the task asked
whether self-subject events are REPRESENTABLE; they are, but the two event
kinds that exist today don't even wire up self-observation for the subject).

`_speech_goal`'s `share` branch (`worlds/bigville_world.py:5530-5536`) already
renders **any** event generically by `kind`/`subject`/`detail` — this branch
needs ZERO changes to carry a self-subject event once one exists and is
observed by its own subject.

### 1.4 — Skill-learning, apprenticeship, crafting, and trading are real, live mechanics — but NONE of them mints an `Event`

`apprentice(learner, master)` (line 6046) and `enrol(pupil, teacher)` (line
6074) are real graph edges (`apprenticed_to`/`attends`) that drive a real,
separately-triggered skill/literacy increment (`worlds/bigville_world.py:
1125-1126`: `self.eng.set_attr(node, "skill", min(master_skill, ... + 0.05))`).
`produce_run`/`sell`/`buy`/`sell_to_shop`/`sell_labor` (lines 6104-6125,
2850, 2940, 2957) are real, live economy actions with real state changes
(items produced, coin exchanged). **Grep-confirmed: none of these methods
calls `create_event`.** "Things I did or learned recently" therefore has NO
existing event-generation hookup for skill/craft/trade content — this is a
genuine absence, not a wiring gap — but it is a SMALL one: each new call site
is a one-line addition mirroring `injure`'s existing pattern exactly
(`create_event(kind, subject=actor, detail=..., observer=actor,
severity=...)`), composing machinery that already works end-to-end for
`injury`/`death`.

### 1.5 — THE HEADLINE FINDING: relationship state itself is NOT populated for the general population in the live town — this blocks sub-claims 3 AND 4, and also the already-shipped gossip mechanism, for anyone outside a hand-configured scenario or test

`set_relationship(a, b, *, kind="acquaintance", strength=1.0, ...)`
(`worlds/bigville_world.py:4535-4556`) is the ONLY code path that populates
`self._relationships[(a, b)]`, which `_speech_relationship` (line 5426) reads
and `_speech_bond` (line 104) uses to set the resident's own held
`Bond.tie_strength` (line 123: `tie_strength = max(0.0, strength)`).

**Grep-confirmed: `set_relationship` is called from exactly nowhere in
production code.** `from_town100` (line 1669) calls only `populate_town100`;
`worlds/bigville_town100_world.py` (the 100-cast generator) contains zero
references to `relationship` or `Bond` at all; `from_scenario`'s own
`supported` key-allowlist for per-actor scenario JSON fields (line 1698,
`{"role", "skill", "station", "literacy", "capability", "learn", "home_cell",
"work_cell", "klass", "age", "life_stage", ...}`) does not include anything
relationship-shaped either. Even within the gossip mechanism's OWN dedicated
test file, only ONE of seventeen tests calls `set_relationship`
(`test_hearing_a_share_increments_the_speakers_told_count_for_that_listener`,
line 184) — every other test either bypasses `decide_speech` entirely
(calling `_speech_share_event`/`_hear_gossip` directly) or doesn't need a
real Argmax outcome.

**A real, hand-authored 22-edge relationship graph already exists for
exactly this purpose and is entirely unconsumed.**
`seeds/bigville_townspeople_50.json` has a top-level `"relationships"` key —
22 `{"src", "edge", "tgt"}` triples (`Mary rival_of John`, `Mary allied_with
Sergeant Bram Cobble`, ...) — but grep confirms this JSON file's name is
referenced by exactly one line in the whole repo
(`worlds/bigville_town100_world.py:158`, a code COMMENT about name-pool
flavour, not a load), and nothing anywhere turns its `relationships` list
into `set_relationship` calls or `Bond` nodes. It is dead data, same category
as the rest of this engine-less repo's unconsumed seed JSON.

**A second, compounding finding: the `stranger` flag `decide_speech` already
branches on (line 169: `stranger → code 0`, forced silence) is hardcoded
`False` at BOTH live call sites** — `resident_speech_proposal` (line 5578,
literal `stranger=False,`) and `_spontaneous_speech_tick` (line 5617, literal
`stranger=False,`). Nobody is ever marked a stranger in the live tick,
regardless of whether any relationship has been set.

**Net effect, stated plainly: in a freshly constructed
`BigvilleWorld.from_town100()`, every resident-resident dyad has
`tie_strength = 0.0`, `stranger = False`, and `affect_resentment =
affect_affection = 0.0` by construction.** `decide_speech`'s branch ladder
therefore collapses, for the entire general population, to: `fpp_is_question
→ answer`, `obligation → greeting`, else `arousal >= loquacity_threshold *
0.25 → smalltalk`, else `stay_silent` — a flat landscape with no relational
variation of ANY kind, including the ALREADY-BUILT `share` gossip term
(`share_salience * tie_strength > 0.2` can never fire with `tie_strength ≡
0`). This is a materially earlier and more general bottleneck than the prior
gossip scoping doc's own "Open Question 3" anticipated ("if agents mostly
stand still... 3.2 alone may produce very little observable gossip") — the
gap is not co-location scarcity, it is that the relational substrate every
bond-weighted term (existing or proposed) reads from is empty for the
general population by default, and always has been.

### 1.6 — No per-dyad/per-group linguistic register state exists — the one adjacent piece of vocabulary found is unexecuted and models a different phenomenon

Grep across the whole repo (`register|familect|idiolect|shared_vocab|
shared_phrase|in-group.*(vocab|phrase)`) turns up exactly one substantive
hit: `seeds/interlocutor_shapes.json`'s `InterlocutorShape` codebook, which
carries a `sig_register` signature dimension (`"formal"`, `"casual"`,
`"neutral"`, `"__none__"`) among several others. Two things distinguish this
from what sub-claim 4 needs: (a) it is a STATIC classification of what KIND
of interlocutor a party appears to be (feeding a self-report-reliability
prior, for theory-of-mind purposes), not a per-dyad state that EMERGES from
shared interaction history between two SPECIFIC residents; (b) grep confirms
`interlocutor_shapes.json` is referenced nowhere in `bigville/runtime.py` —
it is unexecuted seed data, same category as everything else in this
engine-less repo (1.1). No mechanism exists, live or dormant, for two
residents to develop a shared code between just the two of them.

### 1.7 — The rendering pipeline is two-stage, and the SECOND stage (where style would have to live) is currently identity-blind

`_speech_goal` (`worlds/bigville_world.py:5513-5555`) decides WHAT structured
MEANING to say (a small dict, e.g. `{"greeting": {"of": target}}`).
Rendering the literal English happens in a SEPARATE module,
`bigville/runtime.py::WorldAdapter._realize_meaning` (lines 223-286) — a pure
function of the meaning dict alone, with ONE fixed English template per
speech-act key (`"Hello, {target}."`, `"Thank you."`, a 5-entry weather
phrase table, etc.). **`utterance_for(self, meaning)` (line 206) and
`_realize_meaning(value)` (line 223) take no speaker and no listener
parameter at all** — there is no signature slot for register today.

One usable hook already exists, though unused for this purpose:
`BigvilleOcelotActor.goal_utterance` (line 288-303) calls
`self.voice.set_addressee(interlocutor)` before rendering — so the listener's
identity IS already threaded into `WorldAdapter` as instance state
(`self._addressee`) at render time, just never read by `utterance_for`.

**A second, concrete rendering gap directly relevant to sub-claim 2:**
`_realize_meaning`'s `"news"` branch (lines 232-246) unconditionally renders
`f"I heard that {detail}."` / `f"I heard that {subject} {verb}."` regardless
of whether the event's `subject` is the SPEAKER. A self-subject `share` event
would render as "I heard that Anselm was injured" — spoken BY Anselm, about
himself, in the third person — because nothing in the meaning dict or the
renderer currently distinguishes first-person from third-party content. This
is a real, additional, previously unflagged piece of first-person sharing's
cost.

### 1.8 — Bond dynamics knobs already have exactly the right vocabulary for a scaled coupling

`worlds/bigville_bond_world.py::KNOBS` (lines 6-8) already holds
`exposure_weight=0.2` and `gossip_weight=0.5`; `SLOT_DEFAULTS` (lines 10-17)
already holds `tie_strength`. `cohabit(a_name, b_name, encounters)` (line 92)
already shows raw encounter COUNT feeding `tie_strength` via
`exposure_weight` — but this is inside the STANDALONE `BigvilleBondWorld`
harness, not the live `BigvilleWorld` (re-confirms the prior doc's 1.3
finding, still true). There is no standing per-Bond "interaction count"
readable outside that computation — `tie_strength` itself (once populated,
per 1.5) is the only accumulated scalar available to key a threshold on, and
`BigvilleOcelotActor.told_events`/`heard_events` (class `BigvilleOcelotActor`
lines 33/79/87 — a per-`(listener, event)` bookkeeping dict) is the
established, reusable idiom this repo already uses twice for new per-dyad
state (Parts 4 and 5 of the prior gossip doc).

### 1.9 — A directly-relevant, LANDED, MEASURED mechanism exists — but it belongs to OCELOT, not bigville, and bigville deliberately keeps that boundary

Mid-research, the user pointed at a specific, real prior rung and corrected
an initial mis-scoping (the function they meant is `can`, Ocelot's, not
bigville's): `docs/research/engine_substrate/BIGVILLE_CAN_INTEGRATION_PREREG.md`
+ `_RESULTS.md` (ocelot commit `ef8dcca`, "Merge bigville-can-integration:
per-resident belief networks, mixture-drawn resolution trait, GO") is a real,
landed, measured rung, independently re-verified for this doc by reading the
RESULTS file directly. It gave every Bigville resident their own quantized
Causal Attitude Network — a small personal belief network (`Microtheory`/
`Concept` nodes, Ocelot's real Rust `can_ops.rs`) whose representational
RESOLUTION is a per-resident trait: `resolution_bins`, an integer in `[2,12]`
drawn from a two-component Normal mixture (floor/naive `Normal(3.0,1.0)`,
ceiling/exposed `Normal(7.5,2.0)`, `P(ceiling)=0.35`, grounded in real
Cognitive Reflection Test literature), composing with the pre-existing
arousal-driven `resolution_level` state (`effective_bins = max(2,
round(resolution_bins * resolution_level))`) to quantize a continuous "true"
value onto `linspace(-1, 1, effective_bins)`. Measured, not asserted: the
coarse resident's mean quantization error was 9.2× the fine resident's, and
the coarse resident's belief network relaxed to a positive-energy,
highly-frustrated basin while the fine resident's relaxed to a stable,
negative-energy one — under IDENTICAL scenario evidence, with a
population-wide control ruling out confounds. **This is literally "a
quantised codebook over a quantised set of interlocutors" — the exact shape
the user asked this design to reuse — already built and validated, just for
belief-credibility content, not for speech register.**

**It got ORPHANED by the extraction, not merely stale — and re-verified by
direct read, not taken on report alone.** `git show 5065fb8 --stat` (the
"Extract Bigville implementation from Ocelot" commit, run from the ocelot
repo) confirms it deleted `scripts/bigville_can_integration_demo.py`,
`worlds/bigville_can_beliefs.py`, `seeds/bigville_can_beliefs.json`, and
`tests/test_bigville_can_*.py` from ocelot — because they called Ocelot's
real Rust `can_ops.rs` via PyO3 (`_native.Substrate()`), which the
standalone bigville repo does not, and by design should not, depend on
(re-confirming 1.1: bigville's own `bigville/runtime.py` has no
rule-evaluation engine of its own, let alone Ocelot's). Direct read of the
standalone repo confirms only the TRAIT survived: `worlds/
bigville_town100_world.py` still draws a real `resolution_bins` value
(2-12) into every one of the 100 residents in `seeds/bigville_cast100.json`
(`_draw_resolution_bins`, line 142; `tests/test_bigville_world_migrated.py:
1146` asserts `resolution_bins >= 2` on a live actor) — but `effective_bins`/
`quantize_j`, the functions that actually TURN the trait into a discrete
vocabulary and apply it to a value, do not exist anywhere in this repo.

**And — corrected in this same research pass, on the user's own direct
instruction, after an initial mis-scoping — that orphaning is CORRECT
repo architecture, not a bug to fix by porting the quantizer into bigville.**
Direct read of `bigville/backends/ocelot.py`'s own docstring: *"This
package does not import or bundle Ocelot; an external provider can replace
this adapter through the backend factory API."* Bigville deliberately does
NOT bundle real cognition — `bigville/backends/protocol.py`'s
`CognitionBackend` Protocol (`ActorContext` in, `ActorResponse` out) is a
boundary a REAL Ocelot-backed provider is meant to plug into from OUTSIDE
this repo, mirroring Ocelot's own CLAUDE.md architecture rule ("the agent is
Rust, Python is only the world adapter") extended across the repo boundary:
**bigville is the world adapter; Ocelot is where the agent's real cognition,
PSI/CAN included, belongs.** `bigville/backends/psi_can.py`'s
`CANWeightModel` — found and initially misread as a candidate home for this
— is confirmed, on closer reading, to be something else entirely: a small,
standalone, LINEAR weighted-activation scorer over AFFORDANCE CHOICES
(`eat`/`give`/`move`/`work`/...), used by bigville's own deterministic
default backend when no external cognition provider is attached. It shares
the "PSI/CAN" name and nothing else — no quantization, no belief network, no
resolution/bins concept anywhere in it (confirmed by reading `activations`/
`score`/`choose`, lines 71-116) — it is the action-selection analogue of
`decide_speech`'s own hand-coded default, not a home for new register logic.
**The real, validated CAN quantization mechanism — `can_ops.rs`,
`bigville_motivation.json`'s Dörner-PSI/MicroPsi drives, the
`BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md` rung itself — lives, and should
continue to live, in Ocelot's own Rust substrate.** Building it is a
separate, ocelot-repo scoping+build task; it is named here, not designed
here (Part 3.4).

**What IS bigville's job, checked directly: does `ActorContext` already
expose enough for an external Ocelot-side backend to decide style with, or
does it need mechanical, decision-free plumbing added first?** Read
`bigville/game.py::_context` (lines 199-252), the method that builds the
`ActorContext` passed to every backend's `decide()`. Its `observations`
dict already includes `nearby_residents` — a list of `{id, name, role,
position, distance}` per nearby resident (lines 205-217) — and
`heard_utterances(actor)` (the resident's own utterance history). **Neither
carries `tie_strength`, `band_code`, or any relationship/bond information at
all.** An external Ocelot-side backend, today, could see WHO is nearby and
WHAT was said, but has no bigville-supplied signal of HOW CLOSE the speaker
and that interlocutor are — the one input a personality-quantized register
codebook (Ocelot-side) would need FROM bigville to key its bin count or its
band lookup on. This is the concrete, mechanical gap Part 3.4 scopes —
addable via `_band_code` (1.3/1.8: already real, already correct, already
computes exactly this from `tie_strength`, just never called from the live
`worlds/bigville_world.py`) with no new decision logic, only a few new
dict keys per `nearby_residents` entry.

**Checked, not assumed, while establishing the above: none of the 12
existing `_PARAM_SPEC` personality traits already fits "how readily this
resident adopts a shared/familiar register."** `charm_weight`,
`w_supergraph`, `w_spite`, `hostile_weight`, `mood_bias`, `cred_on`,
`claim_weight`, `prior_others_trust`, `prior_self_worth`, `prior_world_safe`,
`valence`, `arousal` — read directly in `worlds/bigville_town100_world.py`'s
`_PARAM_SPEC` — none carries inline semantics documenting a style/
accommodation meaning, and each is already load-bearing for specific
existing drama/economy/credibility formulas elsewhere that repurposing would
silently perturb. This is a fact for whichever repo eventually builds the
mechanism (most likely a new, explicitly-named Ocelot-side trait, mirroring
`resolution_bins`'s own precedent of checking before adding a field) — not
something this doc proposes building, per the correction above.

### 1.10 — Part 1 summary table

| Sub-claim | Verified? | Precise finding |
|---|---|---|
| 1. Topic diversity (role/idiolect) | GENUINELY ABSENT, cheap to add | `role`/`trade` real, held, per-agent — zero references in the speech pipeline |
| 2. First-person experience sharing | GENUINELY ABSENT, representable without new architecture | `create_event`'s subject/observer independence already supports it; NEITHER existing event kind grants self-observation; NO skill/craft/trade action mints an Event at all; the renderer cannot currently distinguish "I..." from "I heard that X..." |
| 3. Talk rate by relationship | GENUINELY ABSENT, and blocked one level deeper than expected | `loquacity_threshold` never coupled to `tie_strength` anywhere; AND `tie_strength`/`stranger` are not populated for the general population at all — the relational substrate a rate term would read from does not exist yet, for anyone outside a hand-configured scenario or test |
| 4. Style convergence ("familect") | GENUINELY ABSENT, and OUT OF SCOPE for a bigville-native build | The real mechanism (quantized codebook keyed on a personality trait — CAN, `can_ops.rs`) already exists, LANDED and MEASURED, but belongs to Ocelot's own substrate by deliberate repo-boundary design (`bigville/backends/ocelot.py`'s own docstring); bigville's job is only to expose enough context (`tie_strength`/`band_code` per nearby resident) for an external Ocelot-side backend to use it — confirmed absent from `ActorContext` today, and addable mechanically |

---

## PART 2 — THE LITERATURE, GROUNDED

### 2.1 — What fills the non-gossip share of conversation, and how much that even is — [HIGH for the qualitative claim, genuinely CONTESTED on the number, reported honestly]

Dunbar, R.I.M., Duncan, N.D.C., & Marriott, A. (1997). "Human conversational
behavior." *Human Nature*, 8, 231-246. Sampling 45 conversations every 30
seconds in public settings, found "social topics" (concerning either those
present or third parties) occupied roughly two-thirds of conversation time
for both men and women, with malicious/critical gossip specifically under 5%.

**Complication, found by this pass and worth reporting because it revises
the number this whole research line has been citing:** Szala, A., Wacewicz,
S., Placiński, M., Poniewierska, A.E., Schmeichel, A., Stefańczyk, M.M.,
Żywiczyński, P., & Dunbar, R.I.M. "How much conversation content is actually
social: human conversational behaviour revisited." *Language and Cognition*
(Cambridge University Press) — a DIRECT revisit, co-authored by Dunbar
himself, of the 1997 study. It finds **~85% social**, not two-thirds — and,
critically for this section's own question, states explicitly that *"the
proportion of 'social' to 'non-social' content in conversation depends
mostly on how 'social content' is defined"* — their own EARLIER pass,
excluding personal experiences from the "social" bucket, found only 50.9%
social. **This directly answers what the "other 35%" is: it is dominated by
personal experience narration, which the definitional boundary of "social"
sometimes includes and sometimes excludes** — this is not a separate
category from gossip so much as a definitional fork inside the same
literature, and it independently corroborates sub-claim 2 (first-person
experience) as the single largest swing factor in what "gossip's share"
even means.

### 2.2 — Occupation/role shapes conversational topic and register, but the clearest evidence is about WORKPLACE talk, not talk ABOUT one's trade elsewhere — [HIGH for workplace register, MEDIUM for the transfer to idiolect]

Drew, P. & Heritage, J. (eds., 1992). *Talk at Work: Interaction in
Institutional Settings*. Cambridge University Press — the foundational
comparison of "workplace talk" against ordinary conversation: goal
orientation, and a distinctive lexis/register per occupation (law vs.
medicine vs. engineering) are established findings. A directly relevant
complication surfaced by the same search pass: research on business/workplace
discourse explicitly notes personal/social topics (family, home, hobbies)
are EXCLUDED from workplace-register talk — i.e. the literature's clearest
occupation→register link is about talk WITHIN the trade context, not a
smith's tendency to bring up smithing IN casual social conversation
elsewhere. **The latter — occupation as a STABLE PERSONAL TOPIC PREFERENCE
carried across contexts — is the genuinely thinner ground**, closer to
"idiolect" (individual, stable, cross-situational linguistic/topical
signature) than to institutional register, but the search pass did not turn
up a canonical single citation establishing occupation-as-topic-preference
specifically outside the workplace, as opposed to occupation-as-register
inside it. Reported as MEDIUM confidence: the underlying phenomenon (people
talk more about what they do) is intuitively and observationally robust, and
gender-topic-preference research (Moore, H.T., 1922, with a 1990 replication
finding the pattern persisted though narrowed — found via secondary source
only, not independently confirmed against the primary text, so flagged
LOW-tier on provenance) shows STABLE topic-preference differences ARE a real,
long-studied object, just not specifically keyed to occupation in the
sources this pass surfaced.

### 2.3 — Self-disclosure of one's own experience is a distinct, established speech function, separate from third-party gossip — [HIGH]

Jourard, S.M. (1971). *Self-Disclosure: An Experimental Analysis of the
Transparent Self*. Wiley (building on his 1964 *The Transparent Self*).
Defines self-disclosure as revealing one's own thoughts, feelings, and
experiences to another, and ties it directly to relationship development —
this is the canonical anchor for sub-claim 2 as a phenomenon separate from
gossip (which is about a THIRD party). Derlega et al. (1993) extend the
definition explicitly to "thoughts, feelings, and experiences" — matching
the user's own framing ("things they did or learned recently") almost
verbatim.

**A genuine, load-bearing complication for the design (Part 3), not merely
background:** Rubin, Z. (1975). "Disclosing oneself to a stranger:
Reciprocity and its limits." *Journal of Experimental Social Psychology*,
11(3), 233-260 (DOI: 10.1016/S0022-1031(75)80025-4) — a classic finding that
strangers RECEIVE MORE intimate self-disclosure than mere acquaintances do
("the stranger on the train" phenomenon: no ongoing relationship means no
reputational stake, so disclosure to a stranger can be safer, not riskier,
than to someone in one's social world). **This means self-disclosure's
relationship to tie strength is plausibly NON-MONOTONIC** (high to close
intimates via Bruess & Pearson-style established trust, high to total
strangers via zero stakes, LOWER to mere acquaintances in between) — a
materially different shape than gossip's own tie-strength-gated Argmax term
(2.4 of the prior scoping doc), which assumes monotonically increasing
willingness with tie strength. This complicates, rather than confirms, the
naive design instinct to reuse gossip's exact coupling term for first-person
sharing (see Part 3's Open Question 1).

### 2.4 — Talk RATE (not just content) scales with tie strength, measurably, in real communication-frequency data — [HIGH]

Roberts, S.G.B. & Dunbar, R.I.M. (2010/2011). "Communication in social
networks: Effects of kinship, network size, and emotional closeness."
*Personal Relationships*, 18(3), 439-452 — call/contact frequency between two
people correlates with self-reported emotional closeness. This is the direct
empirical anchor for sub-claim 3: how OFTEN people talk to someone is itself
a function of tie strength, independent of what gets said. A companion
finding, reported honestly as a complication rather than suppressed: "Call
and SMS Logs Do Not Always Indicate Tie Strength" (ACM, cited via search) —
frequency is a real but IMPERFECT proxy (strong ties without much
communication history exist; weak-tie contacts with high communication
volume exist too) — the correlation is real and directional, not a strict
law.

### 2.5 — Communication Accommodation Theory (CAT) and Audience Design — the load-bearing theories for BOTH rate and style — [HIGH]

Giles, H., Taylor, D.M., & Bourhis, R.Y. (1973). "Towards a theory of
interpersonal accommodation through speech: Some Canadian data." *Language in
Society*, 2. Foundational CAT: speakers CONVERGE toward an interlocutor's
style to seek approval/reduce social distance, or DIVERGE to assert
distinctiveness — **CAT explicitly predicts BOTH directions, not only
convergence**, conditioned on motive (affiliation vs. distinctiveness/
identity assertion). This scoping's Part 3 design proposes only convergence
(matching the user's specific ask about close-friend register), and names
divergence as an explicit, separate, unmodeled prediction of the SAME theory
(Open Question 5).

Bell, A. (1984). "Language style as audience design." *Language in Society*,
13(2), 145-204. A second, closely related anchor: style-shifting is
fundamentally a response to the AUDIENCE — speakers accommodate primarily to
their addressee, with third parties (auditors/overhearers) affecting style to
a lesser, regular degree. This is the more precise citation for WHY talk
differs by addressee specifically (as opposed to CAT's broader convergence/
divergence mechanism).

**A modern, quantitative, directly on-point confirmation of CAT's
convergence half, verified by full fetch, not just search snippet:**
Brinberg, M. & Ram, N. (2021). "Do new romantic couples use more similar
language over time? Evidence from intensive longitudinal text messages."
*Journal of Communication*, 71(3), 454-477. Over 1 million text messages from
41 college-age couples across their first dating year: syntactic (Language
Style Matching), semantic (LSA), and overall vocabulary alignment ALL show
**exponential growth to an asymptote** as the relationship develops — i.e.
convergence is a SATURATING function of accumulated interaction, not a
linear one. This shapes the design in Part 3: `tie_strength` (already
accumulated via `cohabit`'s repeated-exposure term, 1.8) is the right
existing scalar to threshold register convergence on, because its own growth
curve is already the same saturating shape CAT's empirical convergence
literature actually shows.

### 2.6 — In-group/dyadic shared vocabulary has a real name and real citations: "familect" and "relational idioms" — [HIGH]

Gordon, C. (2009). *Making Meanings, Creating Family: Intertextuality and
Framing in Family Interaction*. Oxford University Press — an interactional-
sociolinguistic study of three American families, showing REPETITION as the
mechanism that builds a family's distinctive shared code ("familect" — a
family-specific in-group lect). Bruess, C.J. & Pearson, J.C. (1993). "'Sweet
pea' and 'pussy cat': An examination of idiom use and marital satisfaction
over the life cycle." *Journal of Social and Personal Relationships*, 10(4),
609-615 — 154 couples; satisfied spouses recalled using MORE shared idioms
than unsatisfied ones, and idiom use is HIGHEST in couples married under five
years with no children, declining across the life cycle — i.e. the phenomenon
is real, measured, and non-monotonic across relationship duration (not "more
tie-time always means more idiom," a nuance worth carrying into any threshold
design). Companion citation, corroborating from a friendship (not just
romantic) angle, surfaced by the same search pass but not independently
fetched: Bell, R.A. & Healey, J.G. (1992), "Idiomatic communication and
interpersonal solidarity in friends' relational cultures," *Human
Communication Research* — flagged MEDIUM confidence (title/venue found via
search, not independently verified against the primary text).

### 2.7 — Is a MOTIVATED-COMPUTATION version of any of these four phenomena well-trodden ground in ABM/computational modelling? — [GAP-CONFIRMED, mirroring the prior doc's own gossip-ABM finding]

Karjus, A. & Ehala, M. (2018). "Testing an agent-based model of language
choice on sociolinguistic survey data." *Language Dynamics and Change*, 8(2),
219-. The closest computational precedent found for style/accommodation: a
real ABM of language CHOICE (which of two languages a bilingual Estonian
speaker uses with a given interlocutor), where agents carry
INDIVIDUALLY-CALIBRATED acceptance probabilities for their interlocutor's
language choice, DERIVED FROM real survey data. This is a genuine, working
precedent for accommodation as a per-agent PROPENSITY parameter — but it is
a STATIC, survey-calibrated propensity, not a dynamically GROWING per-dyad
register that accumulates from repeated interaction the way this scoping's
sub-claim 4 (and the Brinberg & Ram 2021 empirical curve, 2.5) describes.
General ABM/social-simulation search otherwise turned up conversation-partner
selection weighted by tie strength (contagion/influence models) and
topic-structured multi-agent conversation simulations, but no purpose-built
model found combines (a) a MOTIVATED, bond-weighted decision to speak AT ALL
that varies talk RATE, or (b) a per-dyad register that GROWS from
accumulated shared interaction (as opposed to a fixed per-agent trait). **This
is the same shape of gap the prior gossip scoping doc found for the decision
to gossip specifically** (Testori et al. 2023's ABM assigns gossip
exogenously, not from a drive) — narrowly confirmed (one focused search pass
per sub-claim), not an exhaustive review, but consistent across four
independent searches this session.

---

## PART 3 — THE PROPOSED DESIGN (mechanism, not labels; reuse, don't invent; scale appropriately)

### 3.1 — What NOT to build, and why

Per 1.5, the single most consequential finding of this audit is that
relationship state does not exist for the general population — NOT that
sub-claims 1-3 lack a plausible mechanism. The wrong move here would be to
treat each as requiring its own bespoke new subsystem (a "topic drive," a
"chattiness drive") when all three can be built as small extensions of
machinery this repo already has working end-to-end
(`create_event`/`observed_event`/`heard_events`, `_speech_share_event`,
`_speech_goal`, `decide_speech`'s existing coupling terms, the
`told_events`-style per-dyad bookkeeping-dict idiom).

**Sub-claim 4 (style convergence) is treated differently below, and this is
a repo-boundary decision, not a difficulty ranking.** Per 1.9, a real,
LANDED, MEASURED mechanism for exactly this shape — a personality-trait-
quantized codebook — already exists (CAN integration, Ocelot's
`can_ops.rs`), but it belongs to Ocelot's own agent substrate by deliberate
design (`bigville/backends/ocelot.py`'s own docstring: bigville does not
bundle cognition; an external Ocelot provider plugs into `ActorContext`/
`ActorResponse` from outside this repo). **This scoping therefore does NOT
propose building sub-claim 4 as bigville-native Python** — porting CAN
quantization math into this repo would reintroduce exactly the coupling the
extraction (`5065fb8`) deliberately removed. Rungs 1-2 below (sub-claims
1-3) are the buildable, bigville-native scope. Sub-claim 4 gets one clearly-
scoped-out deferred item (3.4): only the bigville-side CONTEXT PLUMBING a
future external Ocelot-side backend would need, not the mechanism itself.

### 3.2 — Rung 1: Topic content — idiolect (role/trade) smalltalk + first-person recent-experience sharing

**1a — role/trade smalltalk.** Extend `_speech_goal`'s `smalltalk` branch
(currently `{"weather": {"of": weather}}`, line 5525) to read the SPEAKER's
own `role`/`trade` (already available to the enclosing method scope — a
one-line signature addition, `speaker` threaded through exactly as `target`
already is) and emit a new meaning key, e.g. `{"topic": {"of": trade}}`.
`bigville/runtime.py::_realize_meaning` gets one new branch with a small,
hand-authored phrase table keyed by trade (mirroring the EXISTING 5-entry
weather phrase dict at lines 250-255 in shape and size) — mechanical
template authoring, not a new decision.

**1b — first-person recent experience.** New `create_event` call sites at
skill/apprenticeship-completion and production/trade-completion points,
mirroring `injure`'s existing one-line pattern EXACTLY but — closing the 1.3
gap — passing `observer=actor` this time (`create_event("learned_skill",
subject=actor, detail=..., observer=actor, severity=...)`). These events join
the ALREADY-UNIFIED `_speech_share_event` candidate pool (first-hand +
second-hand, built in the prior doc's Part 5) with **zero changes to that
function**. `_speech_goal`'s `share` branch already renders arbitrary event
`kind`/`subject`/`detail` generically (5530-5536) — **zero changes needed
there either.** The one genuinely new piece: a self/third-party discriminator
(`event.subject == speaker`, computed once inside `_speech_goal`, which
already holds both values) written onto the meaning dict (e.g. `{"news":
{"of": {..., "self": True}}}`), consumed by a new branch in
`_realize_meaning`'s `"news"` handler to render "I..." instead of
unconditionally "I heard that...".

**What's new vs. reused:**

| Component | Status |
|---|---|
| `create_event`'s subject/observer generality | EXISTING — reuse as-is |
| `_speech_share_event`'s unified first/second-hand candidate pool | EXISTING (prior doc's Part 5) — reuse as-is |
| `_speech_goal`'s generic `share` event rendering | EXISTING — reuse as-is, zero changes |
| New `create_event` call sites at skill/production/trade milestones | NEW, mechanical, mirrors `injure`'s one-liner |
| `role`/`trade`-keyed smalltalk meaning + phrase table | NEW, mechanical, mirrors the existing weather phrase table |
| Self/third-party discriminator in the "news" renderer | NEW — a small, necessary addition; without it, first-person sharing renders grammatically wrong |

**Falsifiable predictions:** (a) with the role/trade differentiator forced to
a single constant value across the population, all smalltalk utterances
should be indistinguishable regardless of speaker identity — collapsing to
the current weather-only baseline. (b) with the self/third-party discriminator
disabled, a resident's own first-person achievement should render as a
third-party report about themselves ("I heard that Anselm learned smithing,"
said by Anselm) — a directly observable, wrong-person failure confirming the
discriminator does real work.

### 3.3 — Rung 2: Talk rate scaled by relationship — AND closing the population-relationship-state gap this rung (and the existing gossip mechanism) both depend on

**Prerequisite (mechanical world seeding, not new decision logic).** Turn
`seeds/bigville_townspeople_50.json`'s already-authored 22-edge
`relationships` list (or an equivalent generative pass keyed to household/
workplace proximity in `populate_town100`) into real `set_relationship`
calls at town construction. This is explicitly NOT new gossip-drive or
talk-rate logic — it is data that was already hand-authored for this exact
purpose and simply never consumed (1.5). **Naming it here rather than
silently assuming it: it pays down a debt the ALREADY-SHIPPED `share`
mechanism has also been carrying since it landed** — mirroring the prior
scoping doc's own precedent (3.3 there) of a design rung paying down a
pre-existing residual as a side effect.

**Decision-shape.** Add ONE new multiplicative coupling inside
`decide_speech` between the effective `loquacity_threshold` gate (currently
read as a flat per-agent constant at line 179) and the interlocutor's
`tie_strength` — e.g. `effective_threshold = loquacity_threshold / (1.0 +
accommodation_gain * tie_strength)`, lowering the bar to initiate `smalltalk`
as tie strength rises. This is the SAME shape as the coupling terms already
present in that method (`share_salience * tie_strength`, `affect_resentment`,
`affect_affection`) — one new knob (`accommodation_gain`), zero new state,
zero new node types.

**Falsifiable prediction:** zeroing `accommodation_gain` should collapse
observed talk-initiation rate back to the CURRENT baseline (flat, a function
of arousal vs. threshold only, independent of interlocutor identity) — the
standing falsifier-knob discipline this whole research line uses. With it
non-zero and relationship state populated (the prerequisite above), two
residents with identical `arousal`/`loquacity_threshold` should show a
measurably higher `smalltalk`-initiation rate toward a high-`tie_strength`
interlocutor than toward a `tie_strength≈0` one, given an identical number of
encounter opportunities.

### 3.4 — DEFERRED, not designed: style/register convergence — the real mechanism belongs to Ocelot; bigville's job is only context plumbing, scoped precisely

**This is explicitly NOT a fourth bigville-native rung.** Per 3.1/1.9, the
real mechanism for sub-claim 4 — a personality-trait-quantized codebook
(`resolution_bins`-shaped: a mixture-drawn integer bin count gating how
finely a continuous value, here a register/style choice rather than a belief
weight, gets quantized) applied per discrete relationship band
(`_band_code`-shaped: the already-real 7-band `tie_strength` discretization)
— already exists, landed and measured, as `BIGVILLE_CAN_INTEGRATION_PREREG/
RESULTS.md` + `runners/dsl/src/can_ops.rs`, in OCELOT. Building the
style-convergence analogue of that mechanism (a new quantized "register"
concept alongside the existing quantized "belief" one, keyed on a NEW,
explicitly-named personality trait per 1.9's checked-and-confirmed finding
that no existing `_PARAM_SPEC` field already fits) is a **separate,
ocelot-repo scoping+build task** — named here as a clear pointer, not
designed here, exactly as it should not be attempted as bigville-native
Python.

**What THIS scoping can responsibly design: the bigville-side plumbing a
future external Ocelot-side backend would need, and nothing more.** Checked
directly (1.9): `bigville/game.py::_context`'s `observations["nearby_
residents"]` (lines 205-217) — the one place per-interlocutor information
already reaches `ActorContext` — carries `{id, name, role, position,
distance}` per nearby resident and NOTHING relationship-shaped. The minimal,
mechanical, decision-free addition: extend each `nearby_residents` entry
with `tie_strength` and `band_code` (or `band_code` alone, since it is
already the discrete, codebook-ready form) — a call to the ALREADY-CORRECT
`BigvilleBondWorld._band_code` static method (1.9), reading whatever bond
state `_speech_relationship`/the population-relationship-seeding fix (3.3)
already populates. This is genuinely just exposure — no register decision is
made in bigville; an external Ocelot-side backend receiving `band_code`
would be the thing that decides what to do with it.

**What's new vs. reused, for the PLUMBING only (the mechanism itself is out
of scope):**

| Component | Status |
|---|---|
| `_band_code` (discrete tie-strength band quantizer) | EXISTING (`bigville_bond_world.py:137-147`), correct, just uncalled from the live world — reuse as-is |
| `tie_strength` (once populated by Rung 2's prerequisite, 3.3) | EXISTING — reuse as-is |
| `band_code`/`tie_strength` fields on `ActorContext.observations["nearby_residents"]` | NEW, mechanical, decision-free — a few dict keys per entry |
| The CAN quantized-codebook mechanism itself (`effective_bins`, `quantize_j`, a new register trait) | NOT PROPOSED HERE — belongs in Ocelot's own substrate, a separate scoping+build task, pointer: `BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md`, `can_ops.rs` |
| An external Ocelot-side backend that reads `band_code` and renders register | NOT PROPOSED HERE — the consumer of the plumbing above, built and scoped separately |

**No falsifiable prediction is offered for the deferred mechanism itself** —
this scoping does not design it, so there is nothing here to falsify. The
plumbing addition has its own trivial check: an external backend given the
new `band_code` field should be able to read a real, non-default value once
3.3's relationship-seeding fix lands; with that fix absent, `band_code` would
read `0` for every dyad — the SAME population-flatness failure mode 1.5
already documented, surfaced one layer higher, at the context boundary
instead of inside `decide_speech`.

### 3.5 — Ordering and dependency

Rung 1 (topic content, 3.2) has NO dependency on Rung 2's prerequisite — it
can be built and observed independently, today, in the current unconfigured
town. Rung 2's coupling term (3.3) depends on the population-relationship-
seeding prerequisite named there — building it without that prerequisite
would produce a mechanism that is correct but permanently inert for the
general population, exactly the trap the ALREADY-SHIPPED `share` mechanism
fell into per 1.5. The deferred context-plumbing item (3.4) also depends on
3.3's prerequisite (a `band_code` field is only informative once
`tie_strength` is populated) but is independent of Rung 1, and — being pure
plumbing, not a decision — does not depend on Rung 2's specific coupling
term either, only on the same underlying relationship data.

---

## OPEN QUESTIONS

1. **Should first-person self-disclosure reuse gossip's exact
   `tie_strength`-gated Argmax term, or does Rubin (1975)'s non-monotonic
   stranger-disclosure finding (2.3) mean it needs a DIFFERENT coupling** (a
   floor that stays nonzero even at `tie_strength≈0`, rather than a term that
   vanishes with it)? Rung 1 as proposed reuses the identical `share`
   pipeline without this correction, for minimalism; whether that
   under-fires for casual/stranger self-disclosure specifically is an
   empirical question this scoping surfaces but does not resolve.
2. **Should the role/trade smalltalk phrase table be keyed on `role` (a
   single, closed string) or `trade`/`trades` (which can be multi-valued and
   comma-joined)?** A coverage/scope question, not a structural one.
3. **How dense should the population-relationship-seeding pass (3.3's
   prerequisite) be?** Every pair (N² edges — unrealistic and expensive at
   100 residents) vs. a sparse graph matching the density of the already-
   authored 22-edge `bigville_townspeople_50.json` example (household +
   workplace + a handful of social ties) is a real design-density choice,
   left open here.
4. **Directed vs. shared register, for whichever repo eventually builds
   sub-claim 4.** `Bond` is a directed, asymmetric representation throughout
   this codebase (per the prior doc's 1.3 finding, re-confirmed) — but a
   "familect" is, by definition (Gordon 2009), a SHARED code both parties
   use. Whether a future register mechanism should live on ONE direction of
   the Bond/band (asymmetric, matching the existing pattern, and matching
   how `_band_code` itself is already computed per-direction) or needs a
   genuinely symmetric representation is a real representational tension
   this scoping surfaces but, per 3.4, does not design past.
5. **CAT (2.5) predicts DIVERGENCE as well as convergence** — speakers
   accentuating difference to assert distinctiveness or hostility, not just
   converging for affiliation. Whether the EXISTING `barb`/resentment-driven
   branch in `decide_speech` is a sufficient proxy for relational divergence,
   or whether true STYLE divergence (speaking differently, not just choosing
   a different `kind`, toward a disliked interlocutor) is a separate and
   currently entirely unaddressed mechanism, is open — and, like the
   convergence mechanism itself, most likely belongs on the Ocelot side once
   built, not bigville's.
6. **Is `band_code` (3.4's proposed plumbing field) sufficient context, or
   does a future Ocelot-side register mechanism also need INTERACTION
   HISTORY** (how many prior encounters, not just the current accumulated
   `tie_strength`) **to key its own quantization on** — mirroring how the
   real CAN rung's `effective_bins` composes a TRAIT with a STATE
   (`resolution_level`, arousal-driven) rather than reading a trait alone?
   `heard_utterances(actor)` (already exposed to `ActorContext`, 1.9) may
   already be sufficient raw material for an external backend to derive
   this itself without bigville needing to compute or expose anything
   further — left open rather than assumed either way.

## BUILD LANDED (2026-08-16, `ozmalabs/bigville` commit `719c5e9`)

Rungs 1 and 2 landed as designed. Two findings surfaced only by actually
building and running the code, both fixed:

1. **Town100's relationship-seeding density (Open Question 3) resolved**:
   household grouping turned out to be structurally impossible for town100
   (every resident's `home_cell` is unique by construction), so the real
   proximity signal is workplace CELL, not just workplace kind (25 labourers
   can share one market cell — an all-pairs pass would be a 300-edge clique
   for one profession alone). `seed_workplace_relationships()` links each
   resident to one neighbour per workplace-cell group in a ring: 86 pairs /
   172 directed edges across 100 residents, genuinely sparse, made opt-in
   (not auto-wired into `populate_town100`) since an existing test asserts
   an exact `directed_bonds` count against a bare `from_town100()`.
2. **A second, genuinely pre-existing composition hazard, found only by
   running Rung 2's coupling end-to-end**: `decide_speech`'s own
   `affect_affection > 0 → greeting` branch fires unconditionally on ANY
   positive relationship, on every single encounter, forever — permanently
   outranking the arousal-gated smalltalk branch Rung 2's new coupling
   feeds. A real friendship never reached smalltalk at all, measured 100%
   greeting / 0% smalltalk for a tied pair, before this was fixed. Not
   introduced by this rung — a dormant hazard that had simply never been
   exercised, because `set_relationship` had never been called in
   production code until this same rung's own prerequisite (1) populated
   it. Fixed by reusing already-held state (`speech_choices`, the same
   `told_events`/`heard_events` bookkeeping-dict idiom the gossip work
   already established): a held friendship is a standing REASON to greet,
   not a standing INSTRUCTION to greet every encounter, so greeting no
   longer outranks smalltalk once the pair's last exchange was itself a
   greeting. Verified live: a tied pair now reaches both greeting and
   smalltalk (previously greeting only, 100% of the time); a zero-tie pair
   stays pure smalltalk throughout, unchanged.

17 new tests (`tests/test_bigville_topic_style_migrated.py`) + 193/193
across the whole repo. Sub-claim 4 (style convergence) was not built, per
3.4 — it remains a named pointer to a separate Ocelot-repo task.

## 3.4 CONTEXT PLUMBING LANDED (2026-08-16, `ozmalabs/bigville` commit `1b79a0f`)

The bigville-side half of 3.4 — the only half scoped as bigville-native
work — is built: `BigvilleGame._relationship_signal(actor, other)` reads the
held bond (`world.relationship`, honest `{0.0, 0.0}` floor when unset) and
reuses `BigvilleBondWorld._band_code` verbatim (not reimplemented) to spread
`tie_strength`/`band_code` onto every entry of
`ActorContext.observations["nearby_residents"]`. No register/style decision
is made in bigville — the method returns two numbers, nothing rendered, per
the explicit constraint this rung was built under (rendering belongs
entirely to Ocelot; bigville exposes data only). 4 new tests
(`tests/test_bigville_game_api.py`) cover the floor default, a held tie's
values, agreement with `BigvilleBondWorld._band_code` computed directly, and
that the exposed dict carries no rendered text — 197/197 across the whole
repo. This closes the "confirmed absent from `ActorContext` today, and
addable mechanically" gap the doc itself named at line 417; wiring an actual
Ocelot-side `CognitionBackend` that reads these fields into the
CAN_REGISTER_QUANTIZATION rule remains unbuilt, unrequested follow-on work.

## BOTTOM LINE

The user's four sub-claims are all genuinely true gaps — none of the four is
already secretly built the way the prior scoping doc found the gossip DRIVE
itself already was. But the audit shows something sharper than "four missing
features," and the scope narrowed once during this pass, correctly, on the
user's own direct steer: **three of the four sub-claims (topic content,
first-person experience, talk rate) are bigville-native "mostly wiring"**,
composing cleanly from machinery already built and tested for OTHER purposes
(`create_event`'s generality, the unified first/second-hand
`_speech_share_event` pool, `decide_speech`'s existing coupling-term shape,
the `told_events` bookkeeping idiom) — and **the single most consequential
finding of this whole pass is not about any of the four sub-claims
specifically, but about a shared PREREQUISITE**: relationship state does not
exist for the general population in the live town, at all, and never has,
which means the gossip mechanism the PRIOR scoping doc verified "already
live in the canonical town" is, on this closer read, live only in the sense
that it fires correctly wherever a scenario or test bothers to call
`set_relationship` — it is otherwise as inert as the gaps this doc was asked
to scope. **The fourth sub-claim (style convergence) is deliberately NOT
scoped as bigville-native work**: a real, landed, measured mechanism of
exactly the right shape (a personality-trait-quantized codebook, CAN
integration) already exists, but belongs to Ocelot's own agent substrate by
the same repo-boundary logic Ocelot's own CLAUDE.md states for itself ("the
agent is Rust/Ocelot, Python/bigville is only the world adapter") — this doc
scopes only the small, mechanical, decision-free context plumbing
(`band_code` exposed via `ActorContext`) a future external Ocelot-side
backend would need, and names the mechanism's real build site
(`BIGVILLE_CAN_INTEGRATION_PREREG/RESULTS.md`, `can_ops.rs`) as a pointer,
not a design. The literature (Dunbar/Szala et al.'s definitional-dependency
correction on the gossip-share number, Drew & Heritage's occupational
register, Jourard's self-disclosure distinct from gossip complicated
honestly by Rubin's stranger-disclosure finding, Roberts & Dunbar's
call-frequency-tracks-closeness result, Giles/Bell's accommodation and
audience-design theories, Brinberg & Ram's measured saturating convergence
curve, and Gordon/Bruess & Pearson's familect and relational-idiom research)
grounds all four sub-claims as real phenomena; only three of them are this
document's build proposal. The final shape is **three ordered, bigville-
native rungs — idiolect-flavoured topic content, first-person narrative
reusing the existing event/share pipeline, and talk rate as one new coupling
term paired with the population-relationship-seeding fix the town has needed
since the gossip mechanism first shipped — plus one explicitly deferred
item, named and pointed at, not built here or in bigville at all.**
