# Equilibrium conversation tracking — design (T3c stage O2, pack 0.5.0)

Status: implemented on branch t3c/conversation-tracking (uncommitted). Pack stays
0.5.0 / `eq-tax-0.5.0`: the wire shape is the shared contract O1 already serves
(`basis: "tracked"` was already a legal value); only rule output changes.
Results: `EQUILIBRIUM_CONVERSATION_TRACKING_RESULTS_20261003.md`.

## 1. Problem

O1 removed adjacency as structure. A meeting with no platform-declared replies got
`basis: none` for every turn. On 16 real AMI meetings that meant 12,643 turns,
0 answers and 402/402 questions left open. O2 derives who-responds-to-whom from
the conversation itself. It does this with graph rules only: no LLM, no NLP
guessing of identities, and no Python decisions.

## 2. Mechanism: a seeded turn cursor (new)

Tracking is recursive through negation. Whether turn m answers question q
depends on whether q is still open. That depends on whether an earlier turn
answered q, which depends on that turn's own tracking. A single stratified
fixpoint can't express this. The recursion is stratified by **turn order**, so
the pack carries a cursor:

1. After the S0 fixpoint on the retained fork, the adapter queues each new turn
   (`w -eq_trk_pending-> m`). This is mechanical, like opening a stratum, and the
   edge doubles as the "S0 labels complete" stamp. The adapter then ticks once
   more.
2. `eq.trk.cursor` makes the earliest queued turn current (`w -eq_trk_cur-> m`)
   once no turn is current and its `eq_prev_turn` is no longer queued.
3. The phase rules run on the current turn, in rule order, all in one pass:
   - T1/T2: addressees.
   - T3: tracked targets, written as `eq_trk_to`.
   - T4: answers.
   - T5: state update.
   - Release.
4. Once the queue is empty, `eq.trk.materialise` turns `eq_trk_to` into
   `eq_responds_to` and sets `eq_basis` to "tracked". This is deferred for cost
   only: writing `eq_responds_to` per turn re-enumerated every reply-pair msg rule
   on every cursor pass, which measured 771 ms per batch against 225 ms deferred,
   at 500 turns.

Every negation reads either the current turn's completed S0 labels or state that
earlier turns finalised. Two consequences:

- A turn's tracked structure is **causal**. It is fixed when the turn is
  ingested and never revised by later turns. This answers O1's open decision.
- Incremental batches equal one-shot by construction. This is tested with batch
  sizes 1/3/100 on tracked windows.

The S1–S5 tiers are unchanged. They still run on O1's scratch fork and now see
tracked edges.

Conversation state lives in the graph and only these rules mutate it:

| edge | meaning |
|---|---|
| `w -eq_qud-> q` | open-question set (QUD); addressees = q's `eq_addresses`, none = room |
| `b -eq_pending-> x` | x addressed b; b has not taken a turn since |
| `b -eq_last_addressed_by-> x` | latest turn by another actor addressing b |
| `a -eq_last_claim-> x` | a's latest assertion/directive |
| `m -eq_prev_turn-> p` | ingest ordering edge (cursor + continuation only) |
| `m -eq_continues-> p` | same actor, consecutive turns (feeds `interaction.run`) |

## 3. Rules (seeds/equilibrium_tracking.json, 23 rules + EqSecondPerson codebook)

### Addressees

- **Mention.** A token whose form equals an actor's `eq_name_form` addresses that
  actor. The name form is the actor_ref under the same token normaliser, and is
  set only when the actor_ref is a single token. The actor must already have
  spoken (`eq_first_pos < pos`). This keeps resolution causal, at the cost that
  someone who has not yet spoken can't be addressed by name (see gaps).
- **Second person.** If the turn has no explicit addressee and contains a
  closed-class second-person form, it addresses the author of the latest turn
  that addressed this actor.
- **Declared.** A declared reply still addresses the replied-to author (S0, as in
  O1).
- **Response target.** After T3, the author of each tracked target is added as
  an addressee.

### responds_to (basis "tracked")

Tracking applies only when the turn has no `reply_to`. A declared reply always
wins, including a declared self-reply.

Compatibility means two things:

- The turn's addressees, if it has any, include the target's author.
- If the turn declares a platform_thread, the target is in the same thread.

The target is chosen in this order:

1. **Open question.** The most recent compatible open question for the author:
   one addressed to the author, or to the room. A room question only counts if
   the turn is not itself a question, because a counter-question presupposes
   being addressed.
2. **Pending address.** Only if no open question is compatible: the most recent
   pending address to the author. This "QUD first" ordering means that once a
   counter-question is answered, the question under it is on top again.
3. **Contrasted claim.** Independently of 1 and 2: the most recent claim by
   another actor, if the turn leads with a contrast marker (EqCohMarker contrast)
   or carries msg.concession or msg.disagreement. This reuses the existing scope
   and coherence codebook.

When the turn names addressees, there is one target per addressee group;
otherwise one overall. Several targets are possible. A target can be any number
of turns back.

### answers

A turn answers a question it responds to (declared or tracked) when all of
these hold:

- the question is by another actor;
- the turn is not a nonanswer (a question or withdrawal);
- the turn is not dismissive (a dismissal or hostility cue, or an ungrounded
  status claim).

This is the same shape as the old S1 `eq.win.answers.reply`, which is now
deleted. An answer removes the question from `eq_qud`. `open_questions` is read
out mechanically, unchanged.

### State update

- A question joins `eq_qud`.
- The author's pending addresses are cleared.
- The new turn's addressees get `eq_pending` and `eq_last_addressed_by`
  pointing at it.
- If the turn is an assertion or directive, it becomes the author's
  `eq_last_claim`.

### thread_id

`platform_thread` if given (S0 `eq.win.thread.platform`). Otherwise the cursor
decides it: the thread of the turn's **earliest** parent (a declared `reply_to`
to anyone, or a tracked target), else the turn roots its own thread
(`eq_ref`). This replaces O1's S1 `thread.root` / `thread.inherit` and the
`eq_thread_parent` edges. Those propagated one hop per pass on the scratch fork,
which cost 1.45 s of a 1.5 s S1 tick at 500 turns once tracked chains existed.

### topic_id

Always null. No graph-native lexical-overlap topic shape was built in this stage.

## 4. Consumers rewired

- `inquiry.answered` consumes `eq_answers` and no longer re-derives the shape.
- `interaction.run` consumes `eq_continues`.
- These now see tracked edges with no change of their own:
  - response.dismissal and response.engagement (REPLY over `eq_responds_to`);
  - voice.dissent, inquiry.challenge, reply_contrast and negated echo (S0 msg
    rules over `eq_responds_to`; they fire after materialisation, on the
    retained fork);
  - episodes, responsiveness, question_demand, competence.contested and
    corroborated, and the addressee-targeted cue quanta (S1+ on the scratch
    fork).

## 5. Reused vs new

| | |
|---|---|
| Reused | Retained-fork sessions and scratch-fork strata (O1); EqWindow as the conversation node; declared reply rule; platform-thread rule; the climate cue codebook (nonanswer / dismiss / status / ground) for answer-type; the EqCohMarker contrast codebook; concession and disagreement cue labels; the attr indexes on Message.eq_ref and EqActor.actor_ref. |
| New | Cursor and phase rules; QUD, pending, last-addressed-by and last-claim state edges; EqSecondPerson codebook (11 forms); actor `eq_name_form` / `eq_first_pos` and the ingest `eq_prev_turn` edge; the `eq_trk_pending` queue plus one extra tick per batch. |
| Not reused | `domains/discourse_state.py` / CommonGround. It is a dyadic agent-vs-user faculty with one `pending_expectation`, and its transitions are validated in Python. Reusing it would put the decisions in Python and can't hold N parties. The QUD set plays its "pending expectation closed by a disposition" role as graph state, with one entry per question and per addressee group. |

## 6. N-party and interleaving

- **N parties.** State is per actor (pending, last-addressed-by, last-claim) and
  per room (QUD). Nothing assumes two parties.
- **Interleaving.** Two interleaved room questions are separated by
  `platform_thread` when the platform gives it, or by a name mention.
- **Interleaving without either signal.** The most recent compatible open
  question wins, which can cross threads. This is tested and documented, not
  hidden.
- **Speaking order is never structure on its own.** A statement after a
  statement with nothing open stays `basis: none`.

## 7. Gaps

- **Roster.** The contract carries no participant list, so a person who has not
  yet spoken can't be addressed by name. A `participants` field would fix this
  without breaking causality. AMI speaker ids never appear in the text, so
  mention resolution is about 0 there.
- **Room questions close too easily.** A room question is closed by the first
  answer-type turn from anyone, including backchannels such as "yeah". Telling
  an answer from an acknowledgement needs content (topic/lexical) shapes, which
  are not built.
- **Cue quanta over-target.** Addressee-targeted cue quanta attach to every
  addressee of a multi-target turn.
- **Cost.** One cursor pass per turn: about 85 ms per 100 turns for the tracking
  rules alone at 500 turns, and 225 ms per tick in the full pack. The scratch
  strata now see more edges, so long conversations are slower than in O1 (see
  RESULTS). Engine-side scoped or incremental evaluation is still the fix.
- **topic_id** is always null; there is no lexical-overlap topic shape.
- **Rule order.** Within-pass phase order relies on the manifest's rule order.
  The goldens and the incremental==one-shot tests guard it; no engine-level
  phase primitive is used.

## T3d. Scaling: concurrency, batching, frontier-driven evaluation (pack 0.5.1)

Results and predictions: EQUILIBRIUM_CONVERSATION_SCALING_RESULTS_20261004.md. The wire
is unchanged apart from the version strings (`0.5.1` / `eq-tax-0.5.1`). One endpoint
is new: `POST /v1/conversations/_batch`, which follows the shared batch contract.

**Concurrency** (services/equilibrium_classifier/server.py)

- The global lock is gone. Each conversation has its own lock, so its batches are
  serialised.
- `_meta` guards only the session map, the tombstones and the counters, and is never
  held across engine work.
- All engine work goes through `workers` slots (`--workers` / `EQ_WORKERS`, default
  min(8, cpus)). `/_batch` items run on a thread pool of the same size.
- Threads work because `run_rules` releases the GIL and every fork has its own engine
  mutex. A pre-change probe measured 2.4× at 8 threads. Process pools were not needed.
- A busy session is never evicted: eviction only try-locks.
- The base revision is checked after every request, and the strong digest every N
  requests.

**Engine** (runners/dsl, all flags default OFF, so the committed engine is
byte-identical when they are off)

- `set_batch_incremental`: a `batch` rule takes the semi-naive cursor path. It falls
  back to the full batch pass only on a cold or invalidated cursor, and then installs
  its cursors at the pre-apply frontier. It also admits repeated match edge types,
  deduplicated by the canonical binding key.
- `set_fresh_node_exempt` (the isolated-node exemption):
  - An external `add_node`, or a `set_attr` on a node with no edges, dirties only the
    rules that can see such a node: a Type read, or a non-local opaque read. The
    new `RewriteRule.reads_any_nonlocal` is `reads_any` minus `TypeOf`/`AttrByName`.
  - An external `add_edge` clears the cursors of that edge type's term readers.
- The adapter also turns on `incremental_match`, `precise_dirty` and
  `empty_match_proof`, and keeps per-conversation bookkeeping on an edge-less
  `EqLedger` node.

**Pack** (scripts/_equilibrium_quanta_rules.py `LIVE_L1`/`LIVE_L2`/`apply_live`)

- The monotone strata rules run live on the retained fork, driven by per-batch
  frontier marks:
  - L1: `w -eq_l1-> m`, plus `agent -eq_l1_open-> w` for `eq.ep.extend`. A root turn
    enrols the older turn it answers, so extension must see old turns.
  - L2: `agent -eq_l2_open-> w` + `w -eq_l2-> m` + `w -eq_qnew-> q`. Here `q` is a
    quantum first minted in this batch, found by a ledger set difference. The cue
    counter's `.newq` twin pairs a new quantum with every turn of its author.
- The marks are removed once the layer's fixpoint is reached. A full re-match of a
  live rule therefore sees only the frontier, and a closed layer is skipped by the
  empty-match proof.
- The per-turn window and tracking rules bind the S0 frontier `w -eq_l0-> m`, which
  is removed after the tracking fixpoint. These rules are `eq.win.responds_to.reply`,
  `eq.win.thread.platform`, `eq.trk.materialise` and `eq.trk.continues`.
- `eq.ep.facet` is gated by `eq_l1_open`.
- The non-monotone rules stay on the per-batch scratch fork, unchanged: floor,
  selective non-response, unanswered, claim grounding, generative outcome, match
  shapes, compose.
- Exactness check: all 26 golden runs (351 per-batch responses) captured from the T3c
  code are byte-identical, after normalising 0.5.0 → 0.5.1.

**What remains O(prefix) per batch.** Measured: the 100-turn batch latency
exponent is 1.02 over prefixes of 1k–10k, so per-batch cost is NOT yet sub-linear. It
is about 2× below T3c (see RESULTS). The O(prefix) parts are:

- The S0 msg rules over `agent -received-> m` whenever their cursors are cleared.
  The cause was not established; `neg_op` is one example.
- The scratch tier: its rules bind over all actors, questions, quanta and episodes,
  and the unanswered/responsiveness rules scan later turns.
- `AttrByName` rules: any attr write clears their cursors (per-node predicate
  retraction does not cover dynamic-key reads), e.g. `eq.ep.facet`.
- The read-out: quanta, episodes and open questions are re-read every batch, and
  each emitted row is re-signed.

The next step is retraction rules for the six non-monotone families, so that they
can also run live.

### T3d stage B: the non-monotone families run live (no scratch fork)

The per-batch scratch fork is gone. Every rule now runs on the retained fork, and the
read-out reads the retained fork directly. The read-out after each batch must still
equal a one-shot run over the same prefix. Three things keep that contract
(scripts/_equilibrium_quanta_rules.py, "0.5.1 stage B"):

**Bounded rolling state, finalised by the turn cursor** (equilibrium_tracking, before
`eq.trk.release`):

- **Per-actor turn count.** `eq.trk.nturns` increments `a.eq_nturns` once per tracked
  turn, guarded by `m -eq_counted-> a`.
- **Unanswered wait set.** `w -eq_unans_wait-> q` holds questions no other actor has
  posted after yet. The first later turn by another actor moves the question to
  `q -eq_unans_due-> w`. In steady state the wait set holds only the trailing
  questions of one actor.
- **Non-response wait set.** `a -eq_rsp_wait-> q` holds b's questions to a that a has
  not answered by posting since. a's next turn moves each one to `q -eq_rsp_due-> a`.
  When a responds (declared or tracked), `q -eq_rsp_ans-> a` is added.
- **Episode marks.** For the episode families, each turn's cue role is marked once on
  the L1 frontier: `m -eq_cue_resolve | eq_cue_escalate | eq_cue_extend-> w` and
  `m -eq_fx_cue-> f`. Membership marks `m -eq_ep_res | eq_ep_esc-> e` then feed the
  generative outcome. These marks also replace the dynamic cue look-up and the
  `eq_l1_open` gate of `eq.ep.extend` / `eq.ep.facet`.

**Dedicated retraction edges.** A fact that a later turn can invalidate lives on its
own small edge type:

- `a -eq_nm_quantum-> q`: the quantum exists now. The read-out unions it with
  `eq_has_quantum`.
- `q -eq_evidence_nm-> m`: open evidence.
- `q -eq_counter_nm-> m`: the floor's runner-up turns.
- `q -eq_floor_ru-> b`: the current runner-up.

The monotone parts stay on the committed types: floor evidence (every turn of the
actor) and the answered-question counters. Each family's quantum node is permanent,
linked by `eq_floor_node`, `eq_rsp_node`, `eq_unans_node`, `eq_cg_pos_node` or
`eq_cg_neg_node`. The node accrues its monotone parts whether or not it currently
exists, so when a quantum re-appears it reads exactly the one-shot row.

The retractions:

- **Event-driven.** Unanswered and non-response evidence is retracted when the answer
  edge arrives. This uses `eq_answers` + `enabled(inquiry.answered)`, which is the
  input that `eq.quanta.inquiry.answered` itself consumes.
- **Small candidate sets.** Existence (`*.vanish`), runner-up and runner-up-turn
  retractions match only the dedicated edges.
- **Floor family.** It compares the batch-final copy `a.eq_nturns_b`, taken atomically
  on the L1 frontier. So it sees one state per batch: holder and runner-up flip at most
  once per batch.

**Switching shapes.** Each match-shape rule (quanta exact / partial / weak, composite)
also sets its siblings' provenance to null; the read-out skips null attrs.
Generative resolved / escalated / reopened are mutually exclusive and clear each
other. A facet-match provenance on the episode is cleared once no facet of that
episode holds the shape any more.

**Pack conditions** (asserted by `check_nm_pack` at build time):

- No EqTraitCue row names a non-monotone trait. Cue rules never saw scratch quanta,
  and they must not see the live successors.
- No EqTraitCompose row exists. Composites read `eq_has_quantum` only.

**Engine** (both flags default OFF, enabled only by `incremental_engine` on
conversation forks):

- `set_hop_frontier` refines `write_frontier`'s locality, computed as a second
  install-time variant (`RewriteRule.wf_hop_alt`):
  - `SetT` / `Pick` / `Union` / `Intersect` / `Difference` / `Plus` / `Minus` are
    transparent.
  - An attr read of an `Exists` variable over `Neighbours(v, E)` / `InNeighbours(v, E)`
    of a match variable is one-hop local. A write of that key on x seeds x's
    E-neighbours, e.g. "no facet of e holds shape s" re-checks only e.
  - A `DelEdge` of a type the rule does not match counts as a read at its two bound
    endpoints, so retraction rules can be write-frontier eligible.
- `set_delete_frontier`: a rule-effect `DelEdge (s, E, t)` makes a non-matching reader
  of E re-check only the bindings of s and t, provided every read it makes of E is
  local or is a seedable `AddEdge` of its own. A reader that only deletes E is not
  woken at all. Readers that match E still go stale through the per-type delete
  version. The graph keeps a rule-effect delete log (`edge_delete_log`) for this.

Prefix-proportional work that is left, measured in RESULTS §5:

- the read-out of changed rows, whose evidence lists grow with the conversation (this
  is wire size);
- `eq.competence.corroborated` / `.contested`, whose shape pairs a reply with every
  earlier claim;
- a floor runner-up change, which rewrites O(turns / actors) counter edges. This is
  the size of the wire change.
