# eq-tax-0.8.0 — held-open reply attribution (shared Ocelot <-> Equilibrium contract)

A turn's reply target is no longer forced. Ocelot keeps a bounded set of CANDIDATE
parents per turn, each with the CUES that support it (a closed codebook, no weights,
no floats). It COLLAPSES to a parent only when one candidate DOMINATES every rival
(shape: cue-set strict superset); otherwise the turn is HELD open. Later turns may add
cues to an earlier held turn and collapse it (or supersede it), so turn structure is
revisable and travels as a delta. Confidence is a categorical shape, never a number.

## Cue codebook (closed; strings on the wire)
adjacent        x is the immediately preceding turn by a different actor
open_question   x is an open question compatible with m (addressed to m's author or the room)
addressed       x addressed m's author (pending address) and m's author has not spoken since
vocative        m names (mention / roster alias) x's author
second_person   m is second-person and x's author last addressed m's author
contrast        m leads with contrast / concession / disagreement and x is that actor's last claim
answer_form     x is a question and m has an answer form (polar yes/no to a polar question, etc.)
same_thread     m and x share a platform thread
uptake          LATER: x's author's next turn responds to m (the pair was taken up)
Ocelot may add codes only with a taxonomy bump. Equilibrium rejects unknown codes.

## Confidence (categorical)
declared  platform-declared reply (unchanged semantics)
strong    collapsed; the winner strictly dominates every rival and has >= 2 distinct cues
weak      collapsed; the winner strictly dominates every rival with exactly 1 cue
held      not collapsed: >= 2 candidates and none dominates all rivals (tie / incomparable)
null      no candidates (basis "none")

## Turn object (in `turns` of /turns, _batch items; keys closed)
{"id","labels","responds_to","basis","confidence","candidates","addressees","thread_id","topic_id","answers"}
- basis: "declared" | "tracked" | "held" | "none"
- candidates: [{"ref": <earlier turn id>, "cues": [code, ...]}]  (<= 16 candidates, cues unique, non-empty)
- invariants:
  - basis "none"     <=> candidates == [] and responds_to == [] and confidence null
  - basis "held"     <=> responds_to == [] and len(candidates) >= 2 and confidence "held"; answers == []
  - basis "tracked"  => responds_to non-empty, every responds_to ref is in candidates, confidence in {strong, weak}
  - basis "declared" => confidence "declared"; candidates may be [] (declared needs no cues)
  - refs (responds_to, candidates, answers) are earlier turns of the conversation segment, never self
  - answers only on a collapsed (tracked/declared) turn and subset of responds_to targets that are questions

## Revision: `turns_delta` (new top-level key on /turns, /close and every _batch item; may be [])
[{"id": <earlier turn id of this segment>, "responds_to", "basis", "confidence", "candidates",
  "addressees", "thread_id", "answers"}]
- a FULL replacement of that turn's structure fields (labels / topic_id never change)
  [superseded by Amendment A: topic_id / topic_candidates are revisable; labels never change]
- same invariants as the turn object; only turns already emitted in this segment; one entry per id per reply
- emitted when a later turn (or close) changes an earlier turn's structure: a held turn collapses
  (uptake / new cue), a held turn is superseded (its author spoke again with no resolution: it stays
  held but is FROZEN), or a weak collapse is overturned by new cues
- strong / declared collapses are frozen: never revised
- folding turns_delta over the first emission at every prefix == the one-shot structure (exact)

## Bounds (Ocelot side)
Candidates come only from bounded conversation state (open questions, pending addresses, last claims,
the adjacent other-speaker turn, the addressee's last turn), never a scan of all earlier turns.
A turn stays revisable only while it is in the held frontier (until its author speaks again or close);
per-batch cost must stay sub-linear in conversation length (existing scaling tests and ratios).

## AMENDMENT A (still eq-tax-0.8.0; supersedes conflicting lines above) — questions open TOPICS

Grounding: a question raises an issue (Roberts 1996 QUD; Ginzburg 2012); a simple question
is answered in its second-pair-part slot (Schegloff 2007 adjacency pair), a complex question
shifts the discussion and stays live while people say other things (topic organisation).
Text and speech differ, and turns vary within each, so Ocelot does NOT classify questions as
simple/complex: the RELATION decides — the replying turn's form and position, not the question.

Two relations per turn, each held-open with the same dominance shape:
1. reply (responds_to / candidates): the local sequential prior. An open question is a
   REPLY candidate only when the turn has `answer_form`, or occupies the conditional-relevance
   slot (the selected next speaker's first turn after a question addressed to them; for a room
   question, the first turn by another actor after it). Otherwise the question is not a reply
   rival of the adjacent turn.
2. topic (topic_id / topic_candidates): the live issue(s) the turn is under. Every live issue
   (open question addressed to the author or the room, by another actor, not superseded on its
   bounded pointer) is a topic candidate whatever else was said since.

Topic cue codebook (closed): open_question, via_reply (the turn's settled reply parent is in that
topic, or is the question itself), vocative (names the asker), same_thread, uptake (LATER: a turn
by the asker or by another topic member settles a reply to this turn), answer_form.

Turn object keys (closed) add "topic_candidates": [{"ref": <question turn id>, "cues": [...]}] (<= 16).
- topic_id = ref of the issue-opening question when ONE candidate dominates (strict cue-superset)
  every rival (sole candidate dominates vacuously); else null.
- topic held <=> topic_id null and len(topic_candidates) >= 2; no topic <=> topic_candidates == [].
- topic_id, when set, is in topic_candidates. A question turn itself: its own topic_id is the topic
  it is under (if any), not itself.
- `answers` stays reply-level (simple answers to a question it collapsed onto). A free-form
  contribution is a turn whose decided topic is q, by an actor other than q's asker, that is not
  backchannel-only / nonanswer / dismissive: Ocelot treats q as ENGAGED (not unanswered) once it
  has a contribution; the QUD issue stays live (discussion continues) until superseded or close.
- turns_delta entries now also carry "topic_id" and "topic_candidates" (full replacement);
  topic_id is revisable (the 'labels/topic_id never change' line above is replaced by: labels never change).
- frozen topic: when the turn's topic was decided with >= 2 cues, or via_reply from a frozen reply.

---

## Ocelot implementation notes (pack 0.8.0, T3g; not part of the shared wire contract)

Everything below is graph-native (seeds/equilibrium_tracking.json, generated by
scripts/_equilibrium_quanta_rules.py + scripts/build_equilibrium_seed_pack.py). The adapter
(domains/equilibrium_classify.py) only reads the rules' marks; it never chooses a parent.

Rules, in cursor-phase order (all bind the current turn `w -eq_trk_cur-> m`):
- `eq.trk.adj.prev` / `eq.trk.adj.run`: `m -eq_trk_adj-> x`, the adjacent other-speaker turn
  (previous turn if another actor wrote it, else the previous turn's own `eq_trk_adj`: one
  chain step over a same-actor run, never a scan).
- `eq.trk.addressee.mention` / `.participant` also mark `m -eq_trk_voc-> b`;
  `eq.trk.addressee.second_person` marks `m -eq_trk_2p-> b`.
- candidate sources (undeclared turns only; each writes the proposal `m -eq_trk_cand-> x`,
  every candidate compatible with m's explicit addressees / platform thread):
  `eq.trk.cand.open_question` (QUD top per addressee group), `eq.trk.cand.pending` (latest
  pending address), `eq.trk.cand.claim` (latest other-actor claim, when m leads with
  contrast / concession / disagreement), `eq.trk.cand.adjacent`, `eq.trk.cand.addressee`
  (each addressee's last turn, `b -eq_last_turn-> x`). A source contributes its stack top; no
  source ranks candidates against each other.
- `eq.trk.cand.node`: one fresh EqParentCand per proposal (`m -eq_has_cand-> c -eq_cand_ref-> x`).
- `eq.trk.cue.<code>` (8 rules): `c -eq_cue-> k` for every EqTrkCue code whose predicate holds
  for (m, x). Polar answer_form uses two closed codebooks (EqPolarAux: leading auxiliary of the
  question; EqPolarAnswer: leading yes / no form); otherwise answer_form = x is a question and
  m is an assertion passing the existing answer guards.
- `eq.trk.collapse.strong` / `.weak` / `.held`: dominance shape. `c` dominates `r` iff
  `Not(Exists k in cues(r): Not(In(k, cues(c))))` and `Gt(Count(cues(c)), Count(cues(r)))`;
  collapse iff `c` dominates every rival; strong iff `Gt(Count(cues(c)), |{pick(cues(c))}|)`.
  `eq_trk_conf` = strong | weak | held. No numeric literal, weight or threshold.
- `eq.trk.addressee.target`: the parent's author becomes an addressee only on a STRONG collapse
  (a weak collapse rests on one cue, usually adjacency; the inferred address would feed the
  `addressed` / `second_person` cues of later turns and count that cue twice).
- `eq.trk.answers.declared` / `.tracked`: unchanged guards; a held turn answers nothing.
- `eq.trk.uptake.declared` / `.tracked` / `.held`: m (by a) collapses to / declares a reply to a
  frontier turn p (`pa -eq_trk_held-> p`), or m is HELD with p among its candidates, and a
  authored candidate x of p: `c -eq_cue-> uptake` (once), `m -eq_trk_up-> p`, `w -eq_trk_rev-> p`.
- `eq.trk.late.mark` / `.strong` / `.weak` / `.frozen` / `.answers` / `.qud_close`:
  re-evaluate p with the same dominance shape; a late collapse writes `p -eq_trk_to-> x`,
  `w -eq_trk_late-> p`, and applies only what is still applicable (answer edge, QUD close).
  Strong leaves the frontier. (`.addressee` was removed under Amendment A: see the fix below.)
- `eq.trk.open_q.lapse_for` / `.lapse_room` (read by no rule): an OPEN question superseded on
  its bounded QUD-top pointer by a newer question is recorded `w -eq_qud_lapsed-> q` (eval).
- state updates (`eq.trk.qud.*`, `pending.*`, `addressed_by.*`, `claim.*`, new
  `eq.trk.last_turn.*`) are causal at m's own step, from m's immediate structure.
- `eq.trk.freeze.mark` / `.drop` (DelEdge-only): the author's previous frontier turn leaves the
  frontier (re-emitted once as final); `eq.trk.frontier.enter`: a held / weak m enters it.
- `eq.trk.materialise` (batch frontier) and `eq.trk.materialise.late` (`eq_trk_late` marks):
  collapsed parents become `eq_responds_to` + basis tracked once the queue is swept.

Consequences of the codebook / shape, stated rather than tuned:
- A weak winner is necessarily the SOLE candidate with one cue (a strict subset of a singleton
  is empty; cues are non-empty), so "a weak collapse overturned by new cues" cannot occur: new
  cues (uptake) can only upgrade it to strong on the same parent. `responds_to` is never
  retracted; turns_delta only adds a parent (held -> tracked), raises confidence (weak ->
  strong), adds the `uptake` cue, or re-emits a frozen turn unchanged.
- Uptake collapses a held turn only when the taken-up candidate's cues then strictly contain
  every rival's (e.g. a tie of equal sets); an `adjacent` rival lacking from the taken-up
  candidate keeps the turn held.
- Late collapses do not revise thread ids or touch pending / addressed_by / responsiveness
  state, nor addressees (all causal at the turn's own step). Downstream (quanta / episodes) sees
  the late `eq_responds_to`: the adapter re-layers `eq_trk_late` turns through L1 / L2 with the
  batch's turns, so incremental == one shot after folding.
- Freezing emits a turns_delta entry (unchanged fields) for every turn leaving the frontier
  without a further change (held or weak; author spoke again), and /close emits the remaining
  frontier. /_batch `close:true` appends the close's entries to the item's turns_delta (the
  item's own turns excluded, one entry per id).
- turns_delta never names a turn of the same reply's `turns` (those carry their final
  structure already).
- Candidates are bounded by state: <= 2 + 3 x (named addressees) per turn (QUD top and pending
  top per addressee group, each addressee's last turn, plus adjacent and claim). The 16 cap on
  the wire is validated (a violation is a 500), not truncated.

Held is a legitimate final state, not missing data. A reply chain that is unclear from the
cues may be unclear to the participants as well; a frozen held turn records that ambiguity
(with its candidate set) instead of a guessed edge. Participants resolve their own
ambiguity by uptake (the candidate's author answers the held turn), which is exactly the
revision path; a turn left held until its author speaks again or close was not resolved
in the conversation either. scripts/equilibrium_tracking_eval.py therefore reports the
gold-target rate per final basis and the share of first-held turns later resolved by
uptake, next to recall, and does not treat held as an error to be minimised.

## Held turns take part (0.8.0 rev; grounded in conversation analysis / dialogue theory)

Grounding (one line each):
- Sacks, Schegloff & Jefferson 1974 (turn-taking): a next turn displays its speaker's
  understanding of the prior turn (next-turn proof procedure); next-speaker selection
  (rule 1a: current speaker selects; 1b: self-selection) is realised at the turn's
  transition-relevance place.
- Schegloff 1968; Schegloff 2007 *Sequence Organization*: adjacency pairs, conditional
  relevance of a second pair part, insert expansions, noticeable absence, sequence closing,
  new sequence initiation.
- Ginzburg 2012 *The Interactive Stance*; Larsson & Traum 2000 (information-state update):
  a question stays on the QUD until it is resolved (downdated) or the asker moves on.
- Traum 2004 (multi-party dialogue): addressing, selected addressee vs the room.

Rule changes:
1. Uptake from ANY later turn (SSJ 1974 next-turn proof procedure). `eq.trk.uptake.held`: a
   later turn m by a that is HELD with frontier turn p among its candidates takes p up (its
   structure does not rule p out), so a candidate of p authored by a gains `uptake`, exactly
   as a collapsed / declared m does for its one target. A COLLAPSED m displays one target,
   so only that target is taken up (a collapsed m does not take up its rejected candidates).
   p is re-evaluated with the unchanged dominance shape at m's step; resolution chains
   across later turns (c4 -> c6 in `test_uptake_from_a_held_later_turn_and_chained_resolution`).
   Bound unchanged: only frontier turns (at most one per actor) are revisable; cost is m's
   candidates x p's candidates x the cue codebook; the cue is added once.
2. Turn-dependent vs parent-dependent state (audit). Every state update that depends on the
   TURN ITSELF already fires for a held turn at its own step and is now pinned by tests: a
   held question opens a QUD (a first pair part whatever it responds to; Schegloff 2007),
   addressed to its vocative / mention / roster addressees (qud_for) or the room; a held turn
   takes its author's pending addresses, sets addressed_by / claim / last_turn / run / floor
   counts and responsiveness "actor posted later". Held turns are candidates for later
   turns (adjacent, addressee's last turn, QUD, pending, claim sources read no confidence).
   PARENT-dependent effects wait for the collapse and are applied then if still applicable:
   the answer edge and its QUD close (existing). (This rev also added the parent's author as
   the turn's own addressee on a STRONG late collapse of a non-question, `eq.trk.late.addressee`;
   it is REMOVED under Amendment A -- it broke incremental == one shot, see below.)
   Not applied late (stated, not tuned): (a) a pending address to the parent's author (that
   author is the uptake turn's author and has just spoken: moot); (b) the last-addresser
   pointer (the late address rests on the uptake turn; feeding the second_person cue of
   later turns would count that evidence again -- the same reason a weak collapse infers no
   address); (c) a QUESTION's addressees (they routed it in the QUD as selected next speaker
   vs room at its own transition-relevance place, SSJ 1974 rule 1a / 1b; not re-routed);
   (d) responsiveness wait / answer for a held uptake turn (whether it responded is itself
   held); (e) thread ids (descendants may already have inherited).
3. Possible answers under hold: a held turn's candidates already carry `open_question` /
   `answer_form` on each open question it may answer; nothing is closed until it collapses
   (Ginzburg 2012: downdate on resolution). No new wire field: the consumer counts possible
   answers from the candidate cues.

Relevance lapse (item 1 of the brief) -- decided by the user's direction, recorded here:
a question STAYS LIVE when the addressee (or anyone) says other things. A question opens a
topic and answers are free form; in text (and much of speech) the answer need not be the
next turn, and complex questions shift the discussion rather than calling for one
response. So no rule retires a question as a candidate because of intervening talk (the
addressee's non-answer turn, a new sequence by someone else, the asker speaking again):
each would treat the speech-style adjacency pair (Schegloff 1968) as the only shape of a
question, which the user's direction rules out, and theory does not fix where a "simple"
call / response ends and a topic-opening question begins -- that boundary is HELD OPEN, not
picked (no polar-vs-wh switch, no turn-count window). What remains is the existing bounded
supersession (one QUD-top pointer per addressee / per asker: a newer question replaces an
older one there, the older one staying open, unanswered and live for responsiveness and
for any other source); it is now recorded (`w -eq_qud_lapsed-> q`) and counted by the eval.

AMI test split (aggregates; eq-tax-0.8.0; run once after the change, plus one re-run that
only added the `held_with_uptake_cue` read-out -- no rule changed between them):

| metric | before | after |
|---|---|---|
| responds recall / precision on gold targets | 0.200 / 0.440 | 0.2001 / 0.4401 |
| held share of turns | 0.4918 | 0.4918 |
| held-set coverage | 0.5339 | 0.5339 |
| first-held turns later resolved | 0 / 3698 | 0 / 3698 |
| late-resolution precision on gold targets | -- | n/a (none resolved) |
| held turns carrying an `uptake` cue (taken up, still undecidable) | -- | 1613 |
| questions lapsed (superseded while open) | -- | 64 |
| adjacency baseline recall / precision | 0.476 / 0.488 | 0.4756 / 0.4875 |

Finding: held turns now take part -- 1613 of the 3698 held turns are taken up by a later
turn -- but none resolves, because the dominant held shape (the earlier measurement) is {open question:
open_question, answer_form} vs {adjacent turn: adjacent}; uptake adds one cue to the
adjacent side ({adjacent, uptake}), which still does not contain the rival's cues, and the
strict-superset shape never ranks one cue above another. Whether uptake (the participants'
own display) should decide against an open question's conditional relevance is a choice
theory leaves open here (both are grounded evidence about the same turn) and the contract
forbids a ranking, so it is held open: the consumer sees the `uptake` cue on the held turn.

## Amendment A in Ocelot: questions open TOPICS (pack 0.8.0, T3g)

User direction (verbatim): "It's still live if you say other things - A question starts a
topic, and the answers are free form. Turns in text based conversation vary significantly to
speech, as well as within speech - Simple questions are easy, complex ones are shifts in
discussion, not a call/response."

Diagnosis that motivated it: the dominant held shape on AMI was {open question:
open_question, answer_form} vs {adjacent turn: adjacent(, uptake)} -- a category error. The
question is the TOPIC the turn is under; the adjacent turn is its local reply. They are not
rivals, so no amount of uptake could resolve it.

Grounding (one line each):
- Roberts 1996 (information structure, QUD): every move addresses a question under
  discussion; a question raised stays on the QUD stack until resolved or abandoned.
- Ginzburg 2012 *The Interactive Stance* (KoS): asking pushes an issue on QUD; a resolving
  answer DOWNDATES it; other moves may be about it without resolving it.
- Schegloff 2007 *Sequence Organization*: the adjacency pair -- conditional relevance makes
  the second pair part due in the next slot (the selected speaker's next turn), and its
  type-conforming form (Raymond 2003: yes / no to a polar question) is the "simple" answer;
  insert expansions and post-expansions are sequences inside the base pair's topic.
- Sacks, Schegloff & Jefferson 1974: next-speaker selection (rule 1a: current speaker
  selects -> the selected party's turn; 1b: self-selection -> the first other speaker) fixes
  the slot; a next turn displays its understanding of the prior (in text, the platform reply
  IS that display).

What the rules do (scripts/_equilibrium_quanta_rules.py; all seeded, no Python decision):
1. Reply relation (`_reply_gate`). An open question proposes itself as a reply candidate, and
   carries the `open_question` cue, only when (a) m has the answer FORM -- the type-conforming
   polar relation: the question is led by a polar auxiliary (after any leading vocative,
   "Bea, is ...") and m leads with a polar answer token -- or (b) m sits in the
   conditional-relevance slot: the selected next speaker's first turn after a question
   addressed to them (`a -eq_pending-> x`), or, for a room question, the first turn by another
   actor after it in its sequence space (`x -eq_cr_slot-> w`, opened by the question, closed by
   the first other-actor turn in the same platform thread -- interleaved threads keep their own
   slots; read only through the per-asker pointer, `eq.trk.slot.*`). The question is never
   classified (no polar / wh switch on the QUESTION, no lengths, no windows): the replying
   turn's form and position decide. Consequence: `answer_form` no longer fires for "a
   substantive assertion to a question" -- an assertion is a free-form contribution, i.e.
   the topic relation; in the slot it still replies to (and answers) the question.
2. Topic relation (`eq.trk.top.*`). Candidates (fresh EqTopicCand nodes, `m -eq_has_tcand-> c
   -eq_tcand_ref-> x`, cues `c -eq_tcue-> k` from the closed EqTopicCue codebook):
   the live issues for m's author -- the question on its addressee pointer (`a -eq_qud_for->
   x`) and every other actor's room question on its pointer (`b -eq_qud_room-> x`), by another
   actor -- plus via_reply sources: the settled / declared parent itself when it is a live
   question, and the parent's decided topic when live. Cues: open_question (x is a live issue
   for m's author), via_reply, vocative (m names x's author), same_thread, answer_form (as
   above), uptake (later). Decision by the same strict cue-superset dominance (sole candidate
   vacuously); otherwise topic held. State `eq_top_state` = held | open (decided, revisable: a
   sole 1-cue candidate) | frozen (>= 2 cues, or via_reply from a declared / strong reply).
   Held / open topics enter the author's topic frontier `a -eq_top_held-> m` (one per actor;
   frozen when the author speaks again; re-emitted once). TOPIC UPTAKE: a later turn by x's
   asker or by a topic member of x (`x -eq_tmember-> actor`: authors of turns decided under x)
   that settles a reply onto a frontier turn m adds `uptake` to m's candidate x; m is
   re-evaluated at that step (turns_delta). A 1-cue decided topic is necessarily the sole
   candidate, so a decided topic_id never changes -- only held -> decided, open -> frozen.
3. Engagement (`x -eq_engaged_by-> c`): a turn decided under x by an actor c other than x's
   asker that is not backchannel-only / nonanswer / dismissive. inquiry.unanswered excludes /
   retracts a question engaged by anyone (as "answered by anyone"); interaction.responsiveness
   excludes / retracts it for the actor who engaged it (as `eq_rsp_ans`: a's own response).
   The issue stays live and stays in `open_questions` (no new wire field or status).

Choices made (stated, not tuned):
- Live issue = current on its bounded pointer. Kept the existing pointers: one per addressee
  (the latest question addressed to that actor) and one per asker (its latest room question).
  No extra set was needed: intervening talk never moves a pointer; only a newer question on
  the same pointer does. Bound: |topic_candidates| <= 1 + (other actors with a room question
  on their pointer) + 2.
- Resolution vs engagement: a question answered in the type-conforming form (polar answer to a
  polar question) is resolved and DOWNDATED -- it leaves its pointer (Ginzburg 2012); any
  other reply-level answer (`eq_answers`, a free-form turn in the slot) closes it in
  `open_questions` but leaves the issue live on its pointer: "simple questions are easy",
  "complex ones are shifts in discussion" -- decided by the reply's form, not the question.
- Text vs speech: a platform-DECLARED reply (incl. a declared self-continuation) places the
  turn in its parent's sequence, so its topic candidates are only the via_reply ones (the
  parent question, the parent's topic). Without this, a declared reply into another
  sequence (THREAD golden: "Happy to help." replying to a compliment while a challenge to the
  same author is live) was decided under the unrelated live issue and wiped the selective
  non-response. In speech (no declaration) every live issue is a candidate.
- Topic uptake only from a SETTLED reply onto m (declared / collapsed at the uptake turn's own
  step); via_reply is evaluated at m's own step (a late reply collapse adds no via_reply:
  causal, like thread ids).
- Fix found on the way: the 0.8.0 rev's late addressee (`eq.trk.late.addressee`) made
  incremental != one shot (per-turn evidence reads the ABSENCE of an addressee on the turn's
  own batch: an untargeted quantum stayed after a later address). Removed: addressees are
  causal, fixed at the turn's own step.

Deviations from Amendment A as written (exact):
- D1 (text): for a platform-declared reply, live issues that are not its parent / its
  parent's topic are NOT topic candidates (Amendment A: "every live issue ... is a topic
  candidate whatever else was said since").
- D2: `answer_form` (shared codebook line "polar yes/no to a polar question, etc.") is
  implemented as the polar type-conforming relation only; the earlier 0.8.0 "substantive
  assertion to a question" branch is dropped (it made every assertion a reply rival of
  every open question, the category error the amendment removes).
- D3: engagement for interaction.responsiveness is per actor (the actor's own decided-topic
  contribution), mirroring how "answered" already worked there; for inquiry.unanswered any
  other actor's contribution counts.
- The node type is EqTopicCand (the brief's "EvTopicCand" read as the Eq prefix).
- Not a deviation but a risk: the 16-candidate wire cap is validated (500), not truncated.
  The per-asker room pointers make the topic bound O(actors), so a conversation with more
  than 13 other actors each holding a live room question would exceed it.

AMI test split (aggregates; scripts/equilibrium_tracking_eval.py run once after the change,
plus one re-run that only added the question-detector ceiling read-out -- no rule changed
between them; outputs identical otherwise). "before" = the 0.8.0 rev table above.

| metric | before (0.8.0 rev) | after (Amendment A) |
|---|---|---|
| responds recall / precision on gold targets | 0.2001 / 0.4401 | 0.3387 / 0.4752 |
| strong: recall / precision | not recorded | 0.1653 / 0.5388 (2448 turns) |
| weak: recall / precision | not recorded | 0.1734 / 0.4271 (3929 turns) |
| held share of turns | 0.4918 | 0.1492 (1122 turns) |
| held-set coverage | 0.5339 | 0.5668 |
| first-held turns later resolved by uptake | 0 / 3698 | 0 / 1122 |
| held turns carrying an `uptake` cue | 1613 | 584 |
| questions lapsed (superseded while open) | 64 | 92 |
| adjacency baseline recall / precision | 0.4756 / 0.4875 | 0.4756 / 0.4875 |
| topic: decided / held / none share of turns | -- | 0.5122 / 0.3899 / 0.0979 |
| topic candidates per turn (mean / max) | -- | 2.08 / 5 |
| topic recall, gold el.* pairs: target topic_id = source / source among topic candidates | -- | 0.059 / 0.142 (458 pairs) |
| same, on the 105 pairs whose source Ocelot labels a question | -- | 0.257 / 0.619 |
| Ocelot question turns: engaged / answered / engaged-not-answered | -- | 0.531 / 0.374 / 0.270 (211) |

Reading: removing the question as a reply rival outside its slot cut held turns by 70% and
raised reply recall by 0.14 at higher precision; reply recall is still below the adjacency
baseline (0.476). Topic recall is bounded by question detection: only 105 of 458 gold
elicitation sources are question turns for Ocelot (AMI transcripts are unpunctuated
speech), and a topic can only be opened by a question turn; on those, the source is a topic
candidate of the answering turn 62% of the time and its decided topic 26% (the rest are
held between several live room questions -- in a 4-person meeting each asker's latest room
question stays live). Uptake still resolves no held REPLY: what remains held is mostly the
slot / pending question vs the adjacent turn, which uptake does not order.
