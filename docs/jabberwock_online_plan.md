# Plan: bring the jabberwock online — permanent, pluggable, conversational, self-governing

**North star:** an always-on Rust substrate daemon (the jabberwock itself), checkpointed and
supervised so it runs forever; worlds attach and detach live over an event bus; you talk to and
instruct it through a chat (then voice) world; and it governs its own memory, compute, scheduling,
and behaviour — self-modifying live for anything the DSL can express, with live new-primitive
emission as the named frontier.

The architecture is already shaped for this (agent = Rust graph, Python = world adapters only,
modular dependency-resolved seeds, save/load, JIT hot-load). The plan is mostly *integration + a
daemon + an event bus*, with two honest research edges flagged.

---

## Phase 0 — Make the substrate the only thing running (prerequisite)
- **Build:** an audit + finish-the-migration pass so the live path is `boot(save) -> loop { tick() }`
  in Rust, with **no Python agent logic** — only adapter ingest/emit. Anything load-bearing still in
  the Python `CuriousAgent` moves to graph data or Rust first.
- **Done when:** a full conversation turn runs with zero Python decisions (only `add_node` /
  `add_edge` / `tick` / query).
- **Hard part:** finding what the live path still secretly depends on in Python. A measurement task first.

## Phase 1 — Always-on core (persistence + supervision) — *the spine*
- **Build:** the substrate daemon — boots the latest checkpoint, free-running tick loop on the master
  clock, **periodic checkpoint** (`graph_to_dict` -> SSD, write-temp-then-rename, keep N rotations),
  checkpoint-on-shutdown, **crash-recovery** (boot from latest good snapshot). Supervised by systemd
  (auto-restart, start-on-boot).
- **Done when:** runs a week unattended, survives `kill -9` (resumes with bounded loss), **RSS stays
  flat** (disposable/working/consolidated eviction holds steady-state).
- **Hard parts:** non-blocking checkpoint (CoW snapshot or brief pause-resume); *proving* eviction
  bounds memory over infinite runtime; atomic snapshots (no corrupt file on crash-mid-write).

## Phase 2 — Talk to it (text chat world) — *first contact*
- **Build:** a `ChatWorld` adapter as an **out-of-process client over the event bus** (attaches/detaches
  without restarting the core): type -> ingest `Message`+`Mention` -> `tick()` -> read outbound
  `Message`s -> print. Loads the chat seed closure (core + conversation + intent + referent/pronoun/
  anaphora + psychology + relations).
- **Done when:** you hold a multi-turn conversation with the *persistent* agent over a socket — it
  comprehends, remembers across turns (persistent graph), replies.
- **Hard part:** hardening the end-to-end comprehension stack (recently built, likely brittle); pinning
  the ingest/emit message schema for the bus.

## Phase 3 — Pluggable worlds (runtime registry + lifecycle)
- **Build:** the **event bus + world registry**. Worlds attach/detach live; each declares its seed
  dependency closure; on attach the core resolves + installs seeds (refusing incoherent sets),
  namespaces the world's nodes, routes its events; detach unloads cleanly. Prove it by re-homing an
  existing world (audio, or doom/chess) as a pluggable client.
- **Done when:** you attach a *second* world to the running agent with no restart, it works, you
  detach it, the agent keeps running.
- **Hard parts:** live seed install on a running graph (conflict/coherence check); world isolation/
  namespacing; a stable adapter protocol so each world stays ~50-100 lines.

## Phase 4 — Instruct it (language -> action)
- **Build:** wire the conversation stack to the goal/action machinery — imperative `Message` ->
  `Intent` -> `Goal` -> action in the attached world (the Searle speech-act seed already separates
  question / assertion / instruction). Includes **instructions about itself** ("consolidate memory
  now", "attach the audio world", "explain why you did Y").
- **Done when:** you tell it "do X" in an attached world and it does X — or asks a clarifying
  question, or declines with a reason.
- **Hard part:** robust instruction -> grounded-action (where comprehension brittleness bites hardest);
  self-referential instructions bridge into Phase 5.

## Phase 5 — Complete control over itself
Most layers exist as faculties; this phase **integrates them into the always-on loop** and exposes
them to the agent's own deliberation:
1. **Self-state** — read/write its own rules/concepts/memory (substrate allows; self-improvement loops do it).
2. **Self-scheduling + compute governance** — owns tick cadence, attention, compute budget (cortexes +
   compute-pressure proprioception + RoutingCortex), wired to the daemon clock.
3. **Self-memory** — eviction by value-per-byte (exists), agent-controlled and instrumented.
4. **Live behavioural self-modification** — JIT new Term-trees + hot-load (**already exists** for
   DSL-expressible ops: `jit.rs` / `code_cache` / `l2_adaptive` / `Epoch`-recompile-on-Γ-change);
   confirm it fires in the live loop.
5. **No external cage** — corrigibility + basin-depth, not locks (settled); verify nothing external
   gates self-change.
- **Done when:** the running agent, on its own or on instruction, changes its own behaviour live (adds
  a rule, retunes a basin, recompiles a hot path) with no restart, and holds memory/compute steady-state.
- **FRONTIER (research, not a checkbox):** **live new-primitive self-extension** — emit + hot-load
  native code for a primitive the DSL can't express, live. Today offline (`agent_specify` +
  `emit_primitive_rust` + maturin rebuild + restart). The bare-metal/FPGA path is its hardware
  end-state. Named, not promised this quarter.

---

## Cross-cutting (build alongside, not after)
- **Guardrails that aren't a cage:** the agent perceives compute-pressure *inside*; a **cgroup
  hard-ceiling outside** is the floor so a runaway tick can't take the box down. **Checkpoint-before-
  self-modify** so a bad self-change rolls back. An **append-only audit log of self-modifications** so
  you can see what it did to itself — corrigibility you can read, not control you impose.
- **Observability:** a read-only introspection world — state, memory tiers, compute, recent self-mods —
  its proprioception surfaced to you; also how you *measure* Phase 1's memory bound and Phase 4's
  comprehension reliability.

## Honest sequencing
- **0 -> 1 -> 2 is the MVP:** a permanently-running, checkpointed, crash-surviving daemon you can hold a
  conversation with. The spine; mostly engineering on existing pieces.
- **3** is clean once the bus exists. **4** is the riskiest non-frontier item (comprehension robustness).
  **5** is integration + one research frontier.

## First move (the sysadmin step)
Measure the current live path before writing the daemon: trace what still calls Python agent-logic,
inventory the real boot/tick/save/world-adapter API, and confirm `tick()` + `graph_to_dict` round-trips
a full conversation. That audit turns this plan into a dated task list grounded in what actually runs.

---

## Phase 0 audit — findings (2026-06-17)

The Rust crate is `runners/dsl/` (native module `substrate_rs`, built via maturin). Audit of the
real live path and API:

**Already exists — most of Phase 1/2/3 primitives:**
- **Tick loop / always-on:** `start_agent(tick_rate_hz=10.0, …)` spawns a Rust thread that free-runs
  `tick()` while world adapters write concurrently through the shared `Arc<Mutex<Substrate>>` —
  explicitly *hot-pluggable*, with `agent_stop` (AtomicBool) for clean stop. **Phase 1's loop and
  Phase 3's concurrency model are already in Rust.** (Caveat: `n_runners`>1 not implemented — writes
  serialise today; fine.)
- **Checkpoint:** `graph_to_dict()` / `graph_from_dict()` confirmed to round-trip (proven: Message+
  Mention survive reload; ~210 B for a trivial graph). `persist.rs` = `graph_to_value`/`from_value`
  with an interner (sym-interned attr keys, matching the arena layout). Already exercised in
  `corpus_self_learn.py` (reload into fresh substrate).
- **API:** `add_node`/`add_edge`/`set_attr`/`node`/`nodes`/`neighbours`/`tick`, manifest (seed)
  loading, CAN/basin ops (relax/hebbian/deepen/flatten/beta), memory budgeting
  (`budget_nodes`/`budget_bytes`/`hot_window`), shape recall, composition. Rich and sufficient.
- **Admissibility (Γ) is enforced live:** a bare substrate rejects `Message` until seeds define the
  vocabulary — the grammar check is real, not aspirational.
- **Thin chat adapter exists:** `domains/chat_world.py` (354 lines) — clean `attach`/`add_inbound`/
  `add_outbound`/`quiesce`/`conversation`; calls `load_seeds(agent, ["chat"])` and `start_agent`.
- **A chat runner exists:** `scripts/chat.py` (1023 lines).
- **Cybernetic self-governance stack present:** `l3_mpc`/`l3_lqr`/`l3_kalman`/`l6_essential_variables`/
  `l6_ashby_variety`/`l6_cybernetic_feedback` (Phase 5 substrate).

**The real Phase 0 work (Python agent-logic on the live path):**
- `scripts/chat.py` and the chat container ride on **`CuriousAgent`** (the fat ~13K-line class marked
  for deletion) as the object holding `mind_substrate` + `agent_root`. The deprecated Python rule
  engine (`graph_rewrite`/`gr.run`) is NOT on the conversation path, and `CuriousAgent` is NOT in
  `chat_world` itself — but it IS the live chat *container*.
- `domains/conversation_world.py` (1495 lines) holds genuine **decisions over graph state in Python**
  (`_speech_act`, `_depth_decision`, `_answer_goal`, `_order_n_answer`, `_required_coherence`,
  `_store_fact`) — state lives in the substrate (good, partially migrated) but the decisions don't yet.

**Conclusion / sequencing:** the daemon primitives are ready; the blocker to a *clean* permanent core
is the `CuriousAgent` container. Smallest real first step = a **thin agent container**
(`mind_substrate` + `agent_root` + `load_seeds`, zero decisions) to replace `CuriousAgent` on the
live path, then wrap it in the Phase 1 daemon (boot/checkpoint/loop/supervise). The
`conversation_world` decision→Rules migration is the Phase 0 *tail* (rides as a regression bench
meanwhile, per the architecture rule).

*Status: audit complete.*

## Phase 1 — DONE (2026-06-17): the always-on core works

`scripts/jabberwock_daemon.py` + `deploy/jabberwock.service`, built entirely on primitives
verified end-to-end first. Delivered and tested:
- **Boot/resume:** `CuriousAgent.load(newest-valid-checkpoint)` with crash-recovery fallback
  (corrupt/newer-broken → next older → fresh+`load_seeds(["chat"])`). Resume confirmed faithful
  (agent_root intact, microtheories restored).
- **Free-running loop:** `ChatWorld.attach` → `start_agent(tick_rate_hz)` (Rust thread); confirmed
  `agent_running=True` after boot and after resume.
- **Atomic rotated checkpoint:** quiesce → `agent.save(tmp)` → `os.replace` → keep-N prune.
  ~2.5 MB/checkpoint for the chat agent (matches the SRAM sizing estimate). Microsecond stamps
  (a same-second collision bug was caught by the smoke test and fixed).
- **Graceful shutdown:** SIGTERM/SIGINT → final checkpoint → `stop_agent` → exit.
- **Supervision:** systemd user unit (start-on-boot, auto-restart, `MemoryMax` cgroup ceiling =
  the "guardrail that isn't a cage").
- **Verified:** 3 sequential resumes; a live 6 s run checkpointing every 2 s then SIGTERM-clean.

Remaining for Phase 1 hardening (not blocking): prove RSS stays flat over days (the eviction
bound — instrument node/edge count + RSS), and a non-blocking/CoW checkpoint if quiesce latency
grows with the graph.

**Container note:** the daemon names `CuriousAgent` in exactly two functions (`boot`,
`checkpoint`); the Phase 0 thin-core swap is localized there. Talking to the running agent is
still `scripts/chat.py` (proven) until the Phase 2 socket bus unifies them.

## Phase 2 — DONE (2026-06-17): talk to the running daemon

Three pieces, smoke-tested end-to-end (a separate process held a conversation with the live daemon):
- **`domains/chat_turn.py`** — `respond(agent, world, text)`: a UI-free turn factored from the proven
  chat.py path (ingest → `is_question`? `answer_within` : `agent.receive` → render via the agent's own
  `utterance_for` → outbound → bounded `master_tick` deliberation). No rich/REPL/teacher deps.
- **`jabberwock_daemon.py` socket bus** — a Unix-socket server thread; each request line is one turn,
  serialised against checkpointing by a shared `AGENT_LOCK`. Clients attach/detach live (first
  out-of-process attachable world → Phase 3 seed).
- **`scripts/jbw_talk.py`** — thin client (one-shot or REPL): `python3 scripts/jbw_talk.py "what are you?"`.
- **Verified:** daemon up → `jbw_talk "hello"` → "hello"; `"what are you?"` → "no"; SIGTERM graceful.

**Honest caveat (comprehension grounding):** a fresh `["chat"]`-seed agent answers thinly ("no") to
things it hasn't been taught — the pipe + turn are correct, the *grounding* is absent. chat.py wires a
teacher chain (wiki/LLM/dict) that grounds vocabulary; the daemon deliberately omits it for a minimal
always-on core. Richer answers = attach a teacher/grounding world, or teach it over the socket. This is
the Phase 4 comprehension-robustness work, flagged not hidden.

## Full-entity boot (2026-06-17): the daemon loads EVERYTHING by default

Per "the idea is a full capable autonomous entity", the daemon no longer boots a minimal chat seed —
it boots the whole entity:
- `full_boot()` = `install_full_seed_set` (the ~158-domain foundational stack + agent faculties) +
  world-facing composite seeds + local tools (`_wire_grounding`). `--minimal` opts out for fast tests.
- **Measured (clean):** 158 domains installed, **0 failed**; **184 microtheories, 6,616 concepts**;
  full checkpoint **~7.7 MB**; boot **~20 s** (NOT the multi-minute I first mis-reported off a buffered
  test — the real number is ~7 s seeds + ~12 s attach/settle).
- **Heavy boot is one-time:** restarts resume the fat checkpoint in **~1.6 s** (verified — straight to
  `resumed ←`, no re-install). Slow full boot once → fat checkpoint → fast restarts, as designed.
- **Autonomous:** concepts grew 6,616 → 8,628 across idle runs — the entity does its own work during
  tick windows, and it persists.

**Honest axis-split (loaded ≠ grounded):** the full entity has every faculty and 8k+ concepts, but
conversational answers are still thin ("what is a triangle?" → "no"). Loading all *seeds/faculties* is
not the same as *grounding* — knowing a triangle in produce-able signs needs the teacher/learning loop
(wiki/dict/LLM), which chat.py wires and the daemon defers. So: fully *capable*, conversationally
*untaught*. Wiring grounding (a teacher world / the learning loop) is the next lever — Phase 4.

## Pluggable grounding libraries (2026-06-17): the entity answers richly

`domains/libraries.py` — a pluggable library layer wired into the daemon's `_wire_grounding`:
- **On-disk libraries load by default**, forming the self-teacher chain cheapest-first
  (grammar → dictionary/WordNet → wiki → tropes); each is best-effort (drops out if its data
  isn't on disk). Verified: all four loaded here; "what is a triangle?" → *"(noun) a three-sided
  polygon; synonyms: trigon, trilateral; +4 senses"*. The full entity now answers.
- **LLM is a gated peer** (`--llm`, default OFF): network/key-backed, attached as `agent._llm_partner`,
  consulted by `chat_turn` only on a miss (so the on-disk chain answers first, the network call is last
  resort). Verified default-off: `skipped=['llm (toggle off)']`.
- **Pluggable:** a library is one `LibrarySpec` in `LIBRARIES`; "others come later" = append a spec.
- Teachers are on-disk corpora, NOT graph data → not in the checkpoint → `attach_libraries` runs on
  every boot AND resume.

## Continuous self-teaching (2026-06-17): it learns while idle

`domains/study_loop.py` + the daemon's `cognition_loop`:
- A background thread gives the entity idle cycles — each beat (under `AGENT_LOCK`, interleaving
  cleanly with turns + checkpoints): `master_tick()` (native cognition — reflexes, curiosity,
  teacher-threads) + one `StudyLoop.step` (read a dictionary gloss).
- **StudyLoop** = the proven `ground_unknowns(text)` learning entry, fed reading material: it reads
  the dict gloss for a word the entity knows of, grounds the vocabulary that gloss uses, and
  cascades into the new words it contained — reading the dictionary, looking up what it doesn't know.
  The DECISIONS (discover/ground/meaning) are the agent's; the loop only picks the next thing to read.
- **Measured:** ~30 s idle → **read 192 words, +1,102 signs learned**, frontier 2,280, *and stayed
  responsive* ("what is a wolf?" answered mid-learning). `--think-hz` (rate), `--no-study` (disable).

**Honest caveat (now load-bearing):** active learning grows the graph FAST (~1,100 signs / 30 s →
the checkpoint grew accordingly). The memory-tier eviction/consolidation MUST bound this over a
permanent run, and that is **not yet verified** — it makes Phase 1's "RSS-flat-over-days" the next
real check, not optional. A continuously-learning entity that doesn't forget will OOM; the bound has
to hold.

## Phase 1 hardening (2026-06-17): memory bound under continuous learning

Ran a sustained idle-learning session with RSS + node-count vitals (added to `cognition_loop`,
logged every 20 s — also permanent observability). **Measured: growth is UNBOUNDED** — nodes
climbed linearly 6.7k → 16.4k (~54 nodes/s) while RSS crept 515 → 551 MB. The learner never
forgets; left alone it saturates only when the dictionary is exhausted (hours, multi-GB graph),
and a permanent multi-world entity would OOM. The bound did NOT hold — eviction wasn't running.

**Root cause:** the native eviction (`memory_forget_over_budget` / `observe_and_bound` — keep the
valuable, forget the chaff) is in the Rust *source* (`py.rs`, `memory.rs`) but NOT in the installed
maturin build (`dir(_native.Substrate)` shows no `memory_*`). So nothing could enforce a budget.

**Wired (`--node-budget`, default 1M):** the cognition loop is now budget-aware —
- if the build exposes native CONSOLIDATION → use it (keep learning, forget least-valuable);
- else PAUSE acquisition at the node ceiling.
Verified the pause path (budget 9k): acquisition halts (signs freeze at +1321), **growth drops ~7×**
(54 → ~7.5 nodes/s — the residual is `master_tick`'s own node creation, which pausing study doesn't
touch). RSS stayed ~515–553 MB. So pause-at-budget bounds the dominant source but is not a *hard*
flat bound.

**Correction (creator): "page them out to disk before forgetting."** A permanent learner must NOT
delete what it learned — keep the hot working set in RAM, page cold/low-value clusters OUT TO DISK
(retrievable), never to /dev/null. The faculty already supports this: `memory_consolidate` (record →
durable disk drawer, shape-indexed), `memory_shuffle` (evict cold CLUSTERS from RAM, disk copy
persists), `memory_recall_by_shape` (page back in). `forget_over_budget`/`observe_and_bound` DELETE —
so they're the wrong call.

Two real wrinkles found + fixed: (1) the installed native build was **stale** (the memory faculty was
in `py.rs` source but not compiled in) — forced a real `maturin develop --release` + put the fresh
`.so` where `python3` loads it; (2) the daemon used the wrong handle (`graph._inner` = bare
`_native.Graph`, no memory) — the faculty is on `graph._inner._inner` (`_native.Substrate`, same
graph), reached via `persistence._native_substrate`.

**Corrected bound (verified):** the cognition loop now, over budget, **pages cold clusters out to
disk (`memory_shuffle`) and pauses acquisition — it NEVER calls forget** (0 forget calls confirmed).
A long-term disk store opens at boot. RSS steady ~516–553 MB; still answers under load.

**Honest remaining gap:** page-out only reclaims RAM for clusters that were CONSOLIDATED (shape-
indexed) first. The StudyLoop's learned signs aren't yet grouped into shape clusters, so `shuffle`
currently no-ops and the effective bound is still mostly *pause* (+ a residual ~8 nodes/s from
`master_tick`). To let it learn INDEFINITELY while cold knowledge lives on disk, the consolidate-as-
you-learn flow (group learned signs → `memory_consolidate` → drawers `shuffle` can page out, recall
on access) needs wiring + verifying. Correctness (never delete) holds now; unbounded-learning-with-
paging is the next focused task.

## Reclaim RAM: drop transients (safe) + the lexicon-page-out blocker (2026-06-17)

Censused what grows under learning (+7,399 nodes / 500 study steps): **`drop_disposable` reclaims
~25–30% — all transient `Frame` nodes** (comprehension scaffolding, read-once, NOT knowledge, never
referenced after their tick). Wired it into the cognition loop (every ~2 s, under the lock, between
operations): verified it reclaims continuously (1,854 reclaimed in a 60 s run) and the agent keeps
answering. Safe RAM reclamation — no knowledge touched.

**Lexicon page-out — works but blocked.** Tested consolidate-the-learned-signs → shuffle: it DID
reclaim RAM (node count 11,016 → 8,681, −2,335) — page-out reclaims the lexicon too. **But the agent
then crashed: `KeyError: 'no node #919'`** — a paged-out node is still referenced by active structure,
and `graph.node()` doesn't auto-recall it. So paging out *referenced* knowledge breaks the agent.

**The missing piece (the real next task):** make page-out TRANSPARENT — wire `recall_by_shape` into the
node-access path so `graph.node(nid)` on a paged-out node pages its cluster back in before returning,
instead of `KeyError`. That's a change in the Rust/substrate access path (or its Python shim), not the
daemon. With it, the lexicon can page cold→disk and recall on access — learn forever, bounded RAM,
nothing lost. Until then: `drop_disposable` bounds the transient leak (safe), the lexicon is bounded-
by-corpus (the dictionary is finite), and naive lexicon page-out is NOT wired (it would break the agent).

## Transparent recall-on-access — lexicon page-out is now SAFE (2026-06-17)

The blocker was: paging out a referenced node crashed the agent (`KeyError` on access). Resolved:
- **Verified the enabling mechanic:** `memory_recall_by_shape` restores the SAME node ids even
  across interleaved allocation — so a paged-out node can come back at its original id, edges intact.
- **`substrate/graph.py:node()` recall-on-miss hook:** on a miss (caught from the native `KeyError`),
  call `graph._recall_on_miss(nid)` to page the node's cluster back, retry once. No hook → unchanged.
- **`domains/paged_memory.py` (`PagedMemory`):** consolidates learned concept nodes into shape-
  bucketed disk clusters (`memory_consolidate`), pages COLD clusters out of RAM (`memory_shuffle`,
  disk persists), and installs the recall-on-miss hook with a per-nid→shape map so a miss pages in
  just that bucket (~1/64 of the lexicon), not everything. Nothing deleted.
- **Verified end-to-end:** paged out 547 lexicon nodes (1928→1381), then "what is a triangle?" /
  "what is a wolf?" answered CORRECTLY via transparent recall — agent intact.
- **Daemon bound (verified):** under continuous learning at budget 9k, node count now HOVERS near
  budget (~9.0–9.3k) instead of climbing unbounded (was ~67/s), **learning continues** (signs keep
  growing), it answers correctly under page-out, and **nothing is deleted**. The cognition loop's
  over-budget action is now consolidate→page-out (never `forget`).

**Residual to tighten (refinement, not a blocker):** a slow creep (~15 nodes/s) remains — page-out
lags acquisition slightly (hot_window keeps fresh clusters resident; `master_tick`'s own node
creation; coarse 64-bucket shapes). The bound holds near budget; tightening = smaller hot_window /
page-out more per beat / finer shapes. Correctness (safe, never-delete, learn-while-paging) is done.

## Page-out tuning — the honest physics of the "creep" (2026-06-17)

Tuned: page-out is now PROACTIVE (every ~2 s, not only at budget), hot_window 4→2, and it
consolidates the actually-growing lexicon types — **Lexeme + Concept** (measured: +1.6k each per
400 study steps; the earlier version paged only `_concept_nodes`, missing the 1.6k Lexemes).

But the residual creep does NOT flatten to a flat line at high budget — **and that's correct, not a
bug.** During active continuous learning every freshly-read word is HOT (just created); you can't
page out the working set, only the COLD set. So RAM = working set, and it grows while learning is
active. The bound is enforced AT BUDGET: when the count hits budget, study pauses → recent clusters
cool → page out → resume. Verified earlier at budget 9k: the count HOVERS ~9.0–9.3k (capped, ~3 %
overshoot between per-beat checks), learning continues, it answers, nothing is deleted. That is
proper virtual-memory semantics — bounded at the cap, not a flat line beneath it.

**Operating guidance:** set `--node-budget` to the desired RAM cap; the entity fills the working set
to the cap, pages cold lexicon to disk to stay there, and recalls on access. The "flatten" target was
a misframing — the right invariant is *bounded at budget while learning continues, nothing lost*,
which holds.

## Phase 3 — DONE (2026-06-17): live world registry + lifecycle

`domains/world_registry.py` + daemon socket control commands:
- **`WorldRegistry`** — name → (module, class, seed closure). Registered: `chat` (`["chat"]`),
  `audio` (`["voice"]`); "others come later" = add a `WorldSpec`. (Only ChatWorld/AudioWorld have
  the clean `attach(agent)` lifecycle; the game/task worlds don't yet.)
- **Socket control protocol** — a `/`-prefixed line is a command, anything else is a chat turn:
  `/worlds`, `/attach <w>`, `/detach <w>`, `/help`. Attach loads the world's seed closure
  (idempotent; loader resolves deps + refuses incoherent sets) then `world.attach(agent)` — hot-plugs
  onto the *running* substrate. Detach drops the adapter; the agent keeps running.
- **Verified live on the running daemon:** `/worlds`→`audio, chat*`; `/attach audio`→"attached audio
  (seeds ['voice'])" (second world attached live); `/worlds`→`audio*, chat*`; chat still answers after
  the attach; `/detach audio`→detached; bogus name → graceful error. No restart, agent never paused.

*Next: Phase 0 tail (migrate conversation_world decisions → Rules); give the game/task worlds the
`attach(agent)` lifecycle so they're registrable; Phase 5 (self-control — mostly faculties already
present: l3–l6 cybernetic stack, JIT self-mod, memory governance).*

## Self-modification expansion (2026-06-17) — the agent edits/extends every layer of itself

Creator: expose the JIT (A) + close the new-primitive loop (B) + the agent can EDIT its Python
or MOVE it native (C). The agent is made of layers; full self-control = changing all of them:
  · GRAPH rules/concepts/seeds — already self-rewritten (self-improvement loops).
  · native DSL where-clauses — JIT-compiled to native LIVE (substrate.rs `rule_where_jit` /
    `CompiledWhere`, used in matching; `gamma_epoch` invalidates). Real live binary self-mod;
    just not yet perceivable from Python (layer A = expose it).
  · native PRIMITIVES — `agent_specify_primitive` + `emit_primitive_rust` emit Rust source today
    but stop there (human pastes + rebuilds). Layer B = close the loop autonomously.
  · the PYTHON host (adapters + not-yet-migrated logic) — layer C = edit in place OR move native
    (the ast_to_term/donkey path: Python AST → Term-tree → emitted Rust).

**KEYSTONE built + verified — `domains/self_modification.py`:** guarded self-edit of the agent's
OWN source (444 Python + 60 Rust files). `edit`/`append` → backup → CHECK (py `ast.parse` / Rust
`cargo check`) → ROLLBACK on failure → APPEND-ONLY AUDIT (`var/self_mod_audit.log`); plus
`reload_python` and `rebuild_native` (maturin). Verified: a valid Python edit applies; a broken one
(syntax error) rolls back and the file still parses. The invariant: the agent can experiment on
itself without ever bricking the build. B and C ride on this; nothing mutates without backup+check.

*Next: (A) expose the live rule-where JIT + epoch to Python via a guarded `self_modification` edit to
py.rs + rebuild (agent perceives its native self-opt); (B) autonomous primitive loop on the keystone
(specify→emit→apply→cargo check→maturin→rollback-on-fail); (C) move-Python-to-native via ast_to_term.*

## Self-modification — state after the expansion (2026-06-17)

- **Keystone (committed):** guarded self-edit of all 444 Python + 60 Rust source files
  (backup → check → rollback → audit). Verified.
- **Layer A — jit_report (committed):** the agent can read its rule-where JIT (compiled/total/
  epoch). HONEST FINDING: a chat agent reports 0/0 — its rules are graph-data `Rule` nodes, not
  the Rust engine's `RewriteRule`s, so they don't traverse `rule_where_jit`. Valid hook, off this
  agent's path; the real self-mod is graph-level + source-level.
- **Layer C — edit Python live (verified):** the agent edits its OWN importable code → `reload_python`
  → new behaviour takes effect immediately; a broken edit rolls back and the code still runs. No
  rebuild (Python is live-reloadable). This is the "edit its Python" half of the creator's directive.
- **Layer B — autonomous new primitive (DONE + verified, 2026-06-17):** `domains/self_extend.py`
  (`PrimitiveExtension`) closes the loop autonomously: `agent_specify_primitive` → `emit_primitive_rust`
  → **all-or-nothing apply** → `cargo check` → `rebuild_native` → verify callable → rollback-on-fail.
  A new native `TermNode` touches ~9 sites across `term.rs`/`jsonio.rs`/`reflect.rs` (enum, evaluator,
  copy_subtree, child-index group, json name/parse/group, reflect describe, + the helper fn), so the
  keystone's per-edit `.bak` cannot give all-or-nothing rollback — `self_extend` takes ONE pristine
  snapshot of every touched file first, defers the build check to the end, and on ANY failure restores
  EVERY file byte-for-byte. **Anchors need no line numbers:** the same emit template produces both the
  existing primitive's lines and the new one's, so we emit an ArgMax *anchor* spec (already verbatim in
  the source) and the new spec, then splice each new fragment immediately after its anchor sibling; a
  preflight aborts cleanly if any anchor isn't found verbatim or the primitive name already exists (dup
  guard). **Proven both ways:** (1) `PeakBin` (a new index_of_reduction) applied → `cargo check` passed
  → rebuilt → `evaluate({PeakBin,[3,9,2]})→1`, `[7,1,7,12,4]→3` — the agent CALLED a primitive it had
  just added to its own native vocabulary; then reverted (pure ArgMax-alias, no new semantics — kept
  the source clean). (2) `BrokenBin` (helper references a missing symbol) → `cargo check` rejected
  (E0425) → all 3 files restored byte-identical, primitive absent. Also fixed the `emit_primitive_rust`
  reflect-arm drift (`items: items`→shorthand `items`, matching house style) and the
  `agent_specify_primitive` API breakage (`substrate.node(n)["attrs"]`→`Node.attrs`, `mt.id`) so the
  specify front of the loop runs again.
- **Layer C — move Python → native (DONE + verified, 2026-06-17):** `scripts/python_to_native_closure.py`
  closes the loop the donkey classifier (`scripts/donkey_to_graph.py`) left open. The classifier maps
  each Python compute-core to a Term-tree or a named residual but STOPS there; the closure EMITS the
  native Term-tree AND evaluates it on the Rust evaluator, asserting it equals the original Python.
  Verified faithful for `ema_background` (`0.95*bg+0.05*frame`), `lerp`, `sound_pressure` across inputs
  (native == python to 1e-9) → those donkey functions can be DELETED; the compute is now graph data the
  agent owns. The 4-way verdict routes the rest: held-leaf Calls reimplement an existing Rust op (delete,
  call the op); decision loops/dicts (EMIT-ERROR DictComp etc.) become graph Rules; a genuinely-new
  compute (EMIT-ERROR, no held op) routes to the **Layer B** loop (`agent_specify_primitive` →
  `emit_primitive_rust` → `self_extend.PrimitiveExtension`), which now lands + verifies the primitive
  autonomously. With the verified edit-Python-live half, Layer C is complete.
  **Honest boundary (the map only handles SIMPLE Python):** the fixed AST→Term map covers pure
  expression cores (`Constant/Name/UnaryOp/BinOp/Call`). Complex Python — loops, branches,
  comprehensions, mutation, multi-statement bodies — is NOT translatable. This was worse than a clean
  refusal: `collapse_runs` (a dedup loop) was emitting a bare `Var out`, SILENTLY dropping the loop and
  reporting "graph-native" — a confidently-wrong move. Fixed in `emit_function`: any statement before
  the `Return` now raises `EmitError` (a named residual), so complex Python surfaces as "move me as a
  graph Rule or a new primitive," never as a lossy Term. Verified: `collapse_runs`→residual (Assign
  precedes Return), `tp_table`→residual (DictComp). The move-native path is for compute-cores; decisions
  and control flow remain graph Rules per CLAUDE.md.
- **Layer C — the CORRECTION (2026-06-17): the AST→Term map must be GRAPH RULES, not a Python emitter.**
  Asked to make complex Python *understood and ported* rather than refused, the obvious move was to
  grow `emit_term` into a Python cascade (`if ast_type=='If' → IfThenElse`, `Compare → Eq/Lt`,
  fold-idiom recognition, …). The creator named the irony: *"you are writing Python to get it to have
  less Python."* That cascade IS the agent understanding its own code — composition and decisions — in
  the host language, exactly what CLAUDE.md forbids ("composition in graph, never in Python"). A fixed
  AST-node→Term-type map is a REWRITE SYSTEM, and the substrate already has one in Rust
  (`rewrite::RewriteRule`, `run_rules`/`tick`). So the agent's OWN constitution decides the home (asked
  "where should it live," the creator's answer was *"the jabberwock should decide"* — and its booted
  rule answers): the map is rewrite-rule DATA the agent owns, applied by the Rust engine —
  `ingest_ast` (world-adapter I/O: source→`AstNode` graph) → `tick()` (engine folds AstNode subtrees
  into Term nodes via the rules) → `EvalSubgraph` (eval the graph-resident Term-tree). Feasible with
  EXISTING primitives (`Effect::AddNode`/`AddEdge` build + rewire; `EvalSubgraph` evaluates a graph
  Term) and PROVEN: `scripts/ast_to_term_rule_proof.py` installs one map entry as rule data
  (`Constant→Lit`, value carried) and the engine rewrites an ingested `Constant` into a `Lit` holding
  `5` — by a rule, no Python map. The reverted Python port (`emit_term` cascade) is NOT the answer; the
  full map is more rules of the same shape, ideally agent-generated (a rule-authoring faculty /
  `runtime_design`), and `ast_to_term.py`'s `emit_term`/`AstTermEmitter` is superseded — keep
  `ingest_ast`/`open_ast_productions` (the I/O), retire the Python emitter as the rule set grows.
- **Layer C — the agent GENERATES the rule set (DONE + verified, 2026-06-17):** `domains/ast_term_rules.py`
  holds the only knowledge — the CORRESPONDENCE (Python `Add` MEANS `Plus`, `IfExp` MEANS `IfThenElse`,
  `Compare`+`Gt` MEANS `Gt`, …) — and ONE uniform template (`rule_for`) that expands every row into a
  rewrite-rule dict. NO per-node-type branching (the categorical line vs `emit_term`): the only
  structure is the row's field plan (`leaf` / `items` / `fields`) + an optional `guard` child (a
  matched-but-unwired sibling, e.g. a `Compare`'s op cmpop node) — all DATA. Each rule fires bottom-up
  (matches a parent whose needed children have already `emits`-ed their Term, behind a fire-once
  `Count(Neighbours(p,emits))==0` guard), mints a `Term.<Variant>` node, wires `child.<field>` edges to
  the emitted child Terms, marks the parent emitted. `scripts/ast_to_term_rules_generate.py`: the agent
  generates **16 rules** from 16 rows (arithmetic Plus/Minus/Times/Div/Pow, Neg, Not, comparisons
  Eq/Lt/Lte/Gt/Gte, IfThenElse), installs them, the Rust engine ports real functions
  (`ema_background`, `(a-b)*(a+b)`, `abs = x if x>0 else -x`, nested-ternary `max3`), and `EvalSubgraph`
  evaluates the graph-resident Term — **identical to Python** on every case. The compute moved
  Python→native with NO Python emitter: the map is rule data the agent owns, the fold is the engine's.
  The full map is more correspondence rows of the same shape — BoolOp/Subscript/comprehension as
  expression rows; `Let` (from assignments) and `Fold` (from accumulation loops) as statement-level
  rules — extension is DATA, not code.
- **Layer C — statement-level rules: `Let` + `Fold` (DONE + verified, 2026-06-17):** `ast_term_rules.statement_rules()`
  adds the block-level patterns. These are NOT the uniform per-node template (a statement construct is
  a PATTERN over a statement SEQUENCE), so each is its own explicit rule — still rule DATA the engine
  runs. The block model: a statement `emits` the Term for "the value of the block from here onward."
  `stmt_return_tail` (base case: `Return` emits its value's Term); `stmt_assign_to_let` (`x=expr; <rest>`
  → `Let{name=x, value=expr, body=<rest>}`, firing only when the successor already emits — so it does
  NOT claim an accumulating `For`, which has no emit); `stmt_accumulator_to_fold`
  (`acc=INIT; for v in SRC: acc=EXPR; <rest>` → `Let{acc = Fold(SRC,v,acc,INIT,EXPR) in <rest>}`).
  Consecutiveness in a block is read off the `child_index` attrs (`s2.index == s1.index+1`, same
  parent + `body` field) via a `Plus`+`Eq` where-term — pure structure, no Python. VERIFIED via
  `scripts/ast_to_term_rules_generate.py` (now 19 rules): `t=a+b; return t*t` (Let), two-assignment
  `s=a+b; d=a-b; return s*d` (nested Let), and accumulation loops `sum`/`prod`
  (`acc=0/1; for x in xs: acc=acc±x; return acc` → Fold) — all `EvalSubgraph`-eval identical to Python.
  Remaining map is the long tail of more rows (BoolOp variadic, Subscript, transforming comprehensions,
  conditional-append loop bodies) — same faculty, more data.
- **Layer C — BoolOp + Subscript + comprehension rules (DONE + verified, 2026-06-17):**
  `boolop_rules`/`subscript_rules`/`comprehension_rules` (29 generated rules total). `BoolOp`
  (`a and b…`/`a or b…`) → `And`/`Or{items}`: Python flattens to one variadic node, so one fixed-arity
  rule per (op, N) with an EXACT-arity guard `Count(children)==N+1` (op child + N values) — without it
  a 2-ary rule would fire on a 3-value node and DROP the third (silent loss); arities 2–4 covered.
  `Subscript` `seq[k]` → `Nth{items,index}` for NON-NEGATIVE constant k only — `Nth` casts its index
  `as usize`, so `seq[-1]` would silently become None; from-end indexing stays a residual (a literal
  `seq[-1]` is a `UnaryOp:USub` slice, never a Constant, so the rule can't match it). Comprehension
  `[x for x in src if pred]` (identity elt, single clause/if) → `Filter{source,var_name,predicate}`;
  a transforming comprehension (`[f(x) …]`) has no Map Term → residual. Verified
  (`scripts/ast_to_term_rules_generate.py`): `a and b`, `a or b or c`, `s[0]+s[2]`, `[x for x in xs if x>0]`
  all `EvalSubgraph`-eval identical to Python. **Honest semantic boundary:** `And`/`Or` return a BOOLEAN,
  but Python `and`/`or` return the short-circuit OPERAND — so the BoolOp port is faithful in BOOLEAN
  context (conditions, comprehension `if`, ternary tests), not value context (`x = a or default`). That
  value idiom maps to `IfThenElse`, a later row.
- **Layer C — value-context or/and + transforming/SET comprehension (DONE + verified + a CORRECTION,
  2026-06-17):** Two refinements that also corrected an earlier over-claim. (1) **or/and now use Python's
  OPERAND semantics**: `a or b` == `a if a else b`, `a and b` == `b if a else a`, right-nested for N →
  `boolop_rules` emit nested `IfThenElse` (sharing the value Term across cond+branch; harmless
  double-eval for pure Terms). This is faithful in BOTH value context (`x = a or default`, returns the
  operand) AND boolean context, so it REPLACES the boolean `And`/`Or` shortcut and removes its caveat.
  Verified: `a or b`/`a and b`/`a or b or c` return the operand == Python; boolean-context conditions
  still correct. (2) **CORRECTION — comprehensions are SET-faithful, LIST is a residual**: the DSL's
  iteration Terms `MapSet`/`Filter` return SETS (reorder + dedup) — which IS set-comprehension
  semantics, but NOT list semantics (order + duplicates). The last commit's `ListComp→Filter` was only
  coincidentally right (already-sorted ints, no dups). Corrected: `comprehension_rules` now port SET
  comprehensions only — `{x for x in src if p}`→`Filter`, `{f(x) for x in src}`→`MapSet`,
  `{f(x) for x in src if p}`→`MapSet` over `Filter` (identity vs transforming via a
  `Not(Eq(elt.id,tgt.id))` guard; no-if vs if via `Count(comprehension children)==2|3`). LIST
  comprehensions are NOT ported — a faithful `[…]` needs an ordered map/filter Term the DSL lacks, so
  it's a named residual / Layer-B primitive candidate (ordered `MapList`/`FilterList`), never a
  silently-set port. Verified (`scripts/ast_to_term_rules_generate.py`): set filter/map/map-if eval ==
  Python set (incl. dedup `{2,2,3}`→`{4,9}`).
- **Layer B feeds Layer C — minted `MapList`/`FilterList`, list comprehensions now port (DONE +
  verified, 2026-06-17):** the full circle — Layer C hit a residual (ordered list comprehensions need
  an ordered map/filter the DSL lacked), so Layer B added the primitives. `MapList`/`FilterList` are
  ordered (Tuple-valued) twins of the set-valued `MapSet`/`Filter`: byte-identical except the
  evaluator collects into a `Value::Tuple` (preserving source order + duplicates) instead of
  `make_frozenset`. Added by cloning their twins across every home (enum, evaluator, copy_subtree, the
  free-var/child traversal groups, jsonio name/emit/parse, reflect describe + reconstruct) — they ride
  in their twins' `|`-groups everywhere structural, differing only in the eval arm; `cargo check`
  confirmed full exhaustiveness coverage before the rebuild (shape.rs catch-alls absorb them). Verified
  callable + ordered: `MapList(x*x, [3,1,3])`→`[9,1,9]`, `FilterList(x>2, [3,1,5,2])`→`[3,5]`. Then
  `comprehension_rules` was generalized (`_comprehension_family`) so SetComp→`Filter`/`MapSet` and
  ListComp→`FilterList`/`MapList`; LIST comprehensions now port faithfully WITH order + duplicates:
  `[x*x for x in [3,1,3]]`→`[9,1,9]`, `[x for x in [3,1,5,-2,3] if x>0]`→`[3,1,5,3]`. The Layer-C
  residual is closed by a Layer-B primitive — exactly the intended A↔B↔C loop.
- **Layer C — conditional-append loop body (DONE + verified, 2026-06-17):** the last tail.
  `out = []; for u in SRC: if C: out.append(EXPR); return out` IS a filtered list comprehension, so
  `stmt_conditional_append_to_maplist` ports it to `Let{out = MapList(FilterList(SRC,u,C), u, EXPR)}`
  — reusing the ordered FilterList/MapList primitives just minted, no further Rust. The rule matches
  the deep idiom (init `[]`, a `For` whose body is an `If` of a single `out.append(...)`, then
  `return out`), guarded by `append`-attr + append-target == accumulator + `Count(If children)==2`
  (no else) + block consecutiveness. Required one mechanical world-adapter fix: `ast_to_term`'s
  `_SCALAR_FIELDS` now ingests `attr`, so `Attribute.attr=="append"` is checkable. Verified ordered +
  dups == Python: `out=[]; for x in xs: if x>0: out.append(x*x)` → `[9,4,9]` (== `[x*x for x in xs
  if x>0]`); identity append too. **Honest boundary:** faithful when C and EXPR range over the LOOP
  VAR (+ outer vars). An ACC-DEPENDENT condition (`collapse_runs`' `out[-1] != u`) is NOT ported — it
  needs a stateful scan over an ordered accumulator (last-element / dynamic-index Terms the DSL still
  lacks), so it remains a residual / a future Layer-B item, never a lossy port.
- **Layer B closes the last residual — `Last`/`IndexAt`/`Append`, `collapse_runs` ports (DONE +
  verified, 2026-06-17):** the final loop. Layer B minted three ordered-sequence primitives (cloned
  on the unary `Not` / binary `Union` templates, `cargo check`-guarded, one rebuild): `Last{seq}`
  (last element), `IndexAt{seq, index}` (dynamic index, Python from-end negative semantics — what
  `Nth`'s static `as usize` index couldn't do), `Append{seq, item}` (ordered concat → Tuple).
  Verified callable: `Last[7,8,9]`=9, `IndexAt(-1)`=9, `Append([1,2],3)`=`[1,2,3]`. Then three rule
  upgrades consumed them: (1) `subscript_rules` now emits `IndexAt{seq, <emitted slice>}` for ANY
  index whose slice emits — constant, from-end (`s[-1]`), or dynamic (`s[i]`, `s[i-1]`) — subsuming
  the old non-negative-`Nth` rule and closing the from-end residual. (2) the conditional-append loop
  rule became `stmt_conditional_append_to_fold`: `out=[]; for u in SRC: if C: out.append(EXPR);
  return out` → `Let{out = Fold{SRC,u,out,{}, IfThenElse{C, Append(out,EXPR), out}}}` — the Fold
  exposes the ACCUMULATOR (`acc_name=out`) to C/EXPR, so it handles the acc-dependent stateful scan,
  subsuming the loop-var-only MapList form. (3) added `expr_compare_noteq` (`a != b` → `Not{Eq{a,b}}`,
  the one comparison with no single Term). RESULT: `collapse_runs` — the dedup-consecutive loop with
  `not out or out[-1] != u` — now ports and evals identical to Python (`[1,1,2,2,3,1,1]`→`[1,2,3,1]`,
  empty→empty). The whole driver is 39/39 == Python. The A↔B↔C self-extension loop ran end-to-end one
  more time and the Python-port map has no known residual left in the common expression+statement
  language.
- **Cortex assesses the rule set (2026-06-17):** wired `donkey_to_graph` to port via the GENERATED
  rules (install → `run_rules` → read the body head's `emits`), and the `ArchitectureCortex` now gives
  its OWN verdict on the rule set (`ast_term_rules.assess_rule_set`). The rules live in the engine's
  rule store, not as graph nodes, so the set is represented as a Microtheory whose Concepts ARE the
  rules (each tagged with its family `category` + emitted Term) and the cortex's graph-resident
  quality scorers + smell detectors run over it. Verdict: **54% overall, 0 smells** —
  `separation_of_concerns` 10/10 (34 rules span 8 families), `data_drivenness` 10/10 (every rule
  categorised), no god-object/orphans; but `abstraction_layering` 2/10 and `compositional_reuse` 0/10
  because a flat correspondence map has no Mt-inheritance hierarchy (an honest artifact of the flat
  representation, not a defect — the map is *meant* to be flat). On the donkey set the rules now port
  `ema_background`→Plus and `collapse_runs`→Let/Fold (was a residual), and route held-op/dict-comp
  cases to the Rust op / a graph Rule.
- **Consume `curious_agent.py` (2026-06-17):** `scripts/consume_curious_agent.py` runs ALL 456
  functions of the 18.5k-line `CuriousAgent` (the class CLAUDE.md marks for deletion) through the
  agent's own rule porter (fresh substrate per fn; `add_rule` only — rule effects bypass the grammar,
  so no production matrix; functions > 120 AST nodes diagnosed statically since a large body is a
  loop/decision by construction). VERDICT — the migration map: **PORTED 0%, STATE 87.1% (397 read/
  write `self.<attr>` → decision+state → a graph RULE), CALLS 7.9% (compose faculties → Rules/
  sub-Terms), DICT/COMP 2.4% (→ a graph Rule), HELD-OP 2.2% (10 fns reimplement a Rust op, e.g. `abs`
  → delete, call the op), RESIDUAL 0.4%.** ZERO functions are pure compute that folds to a native
  Term — `CuriousAgent` is entirely agent logic + state, which is exactly why it's replaced WHOLESALE
  by graph data (Rules/Concepts), not hand-ported. The "fix" is therefore re-expression as Rules, not
  a per-function port; the only delete-and-call fixes are the 10 held-op duplicates. The porter
  consuming the real 18.5k-line agent — and finding nothing to port — is itself the evidence that the
  CLAUDE.md migration (delete the Python agent, keep only world-adapters) is the right call.
- **…but the STATE→Rule migration is ~90% MECHANICAL (2026-06-17, a correction):** "0% ports to a
  compute Term" is NOT "hand-rewrite." A stateful method has a mechanical shape that maps to a
  RewriteRule: `if C: self.x = e` → `where=Term(C)`, `effect=set_attr(self, x, Term(e))`;
  `obj.attrs[k]=e` → `set_attr`; `coll.add/append(t)` → `add_edge`; `tx.add_node/add_edge` →
  `add_node/add_edge`; `for v in coll` → match over the collection; `return e` → the produced value
  — and the where-conditions + value expressions reuse the AST→Term rules. `scripts/mechanize_curious_agent.py`
  classifies every statement: **6006/6611 statements (90.8%) map to a known Rule shape**
  (2605 set_attr/let, 1163 if→where, 716 return, 471 for→match, 354 add_edge, …); **215/456 functions
  (47%) are FULLY mechanical.** The ~9% residue is the genuine judgment — external library `call`s
  (320), `With`/`Try`/`While`/`Import`/`raise` — plus the match/trigger wiring. So the migration is
  mostly a mechanical statement→Effect/where translation (the next tool to build), not a rewrite; only
  the residue needs hand work. The two findings reconcile: a method doesn't fold to ONE compute Term
  (it's not pure), but its statements DO translate mechanically to Rule effects + where.
- **BUILT the migrator — and the 90% does NOT hold up (honest correction):** `domains/ast_to_rule.py`
  (`Migrator`) realises the translation: expressions are composed BY THE RULES (ingested, folded, then
  read out to Term-JSON via `term_to_json` — serialisation of already-composed graph data, NOT a
  Python emitter; an `Attribute`→`Attr` rule was added so `self.x` composes), and statement shells map
  to engine Effects (`self.x=e`→`set_attr`; `coll.add/append`→`add_edge`; `if C`→`where`). The
  mechanism is REAL: migrated rules are engine-accepted AND fire — `bump`
  (`if self.score>=self.best: self.best=self.score`) mutates `best 3→7` when the guard holds, blocked
  otherwise. BUT over all 456 methods (`scripts/migrate_curious_agent.py`): **CLEAN 3 (0.7%), PARTIAL
  399, QUERY 54; aggregate 81 effects translated vs 2412 residual ≈ 3% of mutating statements migrate
  by machine.** The 90.8% was a SHELL-level count (a statement *looks* like `set_attr`); the real
  yield is ~3% because the VALUES are overwhelmingly faculty/library calls (`self.foo(...)`, `np.*`,
  dict-comps) that don't compose to a Term. Honest verdict: the migration is mechanical in SHELL but
  NOT in SUBSTANCE — the substance is faculty composition (the genuine work). "~90% mechanical" was
  true of the shapes, false of the actual translation once built. The migrator does the mechanical ~3%
  for real (verified firing); the rest is composition + the match/trigger judgment.
- **Call distribution — the migrator's 3% was coverage, not the ceiling (2026-06-17):**
  `scripts/call_distribution.py` classifies all **6742 call sites** in curious_agent.py. **81.9% are
  MECHANICAL-class**, not faculty composition: Term/DSL constructors (28% — `Var`/`Attr`/`Lit`/
  `NodePattern`/`Production`/`Eq`, the agent building graph data in Python), collection/attr ops (21%
  — `.get`/`.append`/`.items`), builtins (18% — `len`/`min`/`max`/`int`/`float`/`isinstance`), graph
  ops (13% — `mind_graph.node`/`tx.add_edge`/`out_edges`), np.* (mechanical). Only **~14% is genuine
  FACULTY** (`self.method()` + bare locals) — a SMALL enumerable set: `_get_scalar_policy`(73),
  `_term_to_mind`(33), `_spec_to_term`(20), `_ema_update`(17), `_create_goal`(14), … So the migrator's
  3% under-counted because it didn't translate the mechanical call CLASSES (constructors → the very
  Terms the rules emit; graph ops → Effects/reads; collection ops/builtins → held ops). Added the
  np/math-call rules (`np.abs`→`Abs`, `np.dot`→`UseTool{dot}`, bare `abs/sqrt/log/exp`; `self.foo()`
  stays residual) — composition verified. The honest convergence: ~80% of the work is mechanical
  (build graph data + graph ops + builtins), the irreducible ~14% is the enumerable faculty set →
  Rules or kept primitives. So the creator's "~90% mechanical" holds at the CALL level once the
  mechanical classes are handled; my "3%" was the tool's coverage, not the limit.
- **Migrator: constructor recognition + the converged picture (2026-06-17):** extended
  `ast_to_rule.Migrator` to RECOGNISE the agent's Term-constructor calls — `Eq(Attr(Var("type"),"x"),
  Lit(0.4))` transcribes directly to its Term-JSON (a fixed table of the substrate's Term API,
  recursing on sub-term args, falling back to the engine rules for genuine Python sub-exprs). That is
  the agent hand-building Term-JSON in Python, read back out. Re-running over 456 methods: OPAQUE
  dropped ~88%→49.6% (the calls ARE mechanical), PARTIAL rose to 48%, but FULLY-mechanical whole
  methods only 2.4% (CLEAN 3 + MECH-QUERY 8). THE CONVERGED, GRANULARITY-AWARE TRUTH: mechanical at
  the CALL/STATEMENT level (~80–90%), rare at the whole-METHOD level (2.4%) — because nearly every
  method MIXES ~80% mechanical calls with a small faculty/control residue (10 mechanical calls + one
  `self._spec_to_term()` = PARTIAL, not CLEAN). So the migration UNIT is NOT the method and NOT
  "auto-convert the file"; it is: mechanically transcribe the bulk of each method (constructors →
  Terms, graph ops → Effects, builtins → held ops) and hand-resolve the ~15% enumerable FACULTY calls
  (`_spec_to_term`/`_term_to_mind`/`_ema_update`/… a few dozen methods → Rules or kept primitives) +
  the match/trigger. "Mechanical in the small, mixed in the large" — a straightforward, bounded
  migration once measured at the right granularity.
- **The faculty worklist — the bounded hand-work, enumerated (2026-06-17):**
  `scripts/faculty_worklist.py` lists the 357 distinct faculty methods (of 1136 faculty call sites;
  the other ~80% of the file is mechanical) and classifies each by what it BECOMES:
  **RULE 95** (writes self-state → a graph Rule), **COMPOSITION 94** (calls other faculties → a Rule
  firing sub-Rules), **REVIEW 80** (the genuine judgment core), **GRAPH-BUILD 70** (tx/mind_graph
  add_node/edge → Rule effects), **FACTORY 18** (returns a Term → a derived attr/seed). So even inside
  the faculty residue, 183 (RULE+GRAPH-BUILD+FACTORY) are FURTHER mechanical-class, 94 are structural
  glue, and the IRREDUCIBLE judgment is ~80 REVIEW methods (`_get_scalar_policy`, `_get_top_level_goals`,
  `action_kind_primitives`, `_calibrated_step`, …). Final bounded shape of the migration: ~80% of the
  file transcribes mechanically (constructors→Terms, graph ops→Effects, builtins/np→held ops); of the
  faculty residue, the bulk is further-mechanical (Rules/effects/factories) and the true hand-judgment
  is ~80 decision faculties → Rules. The 18.5k-line "delete CuriousAgent" migration is, concretely, a
  few-dozen-faculty job — exactly the shape the creator read from the start.
- **Migrator coverage raised + the three honest numbers (2026-06-17):** extended the migrator to
  translate graph-build statements — `nid = tx.add_node(TYPE, {attrs})` → `add_node` effect (binds
  nid), `tx.add_edge(src,"e",tgt)` → `add_edge`, unwrapping `with …transform() as tx:` (a no-op in
  the engine). Verified: a synthetic ensure-method migrates CLEAN + engine-accepted. Re-run over 456:
  per-statement yield rose **3% → 11%** (319 effects/values translated vs 2490 residual). THREE
  numbers, three depths — say which you mean: **90.8%** statement SHAPES look mechanical; **82%** CALL
  SITES are mechanical-class (the structural ceiling); **11%** my BUILT migrator actually emits an
  effect/value end-to-end. The 11→82 gap is a LONG TAIL of statement-shape coverage the migrator
  doesn't yet walk (local `x=…` bindings → `Let`-threading, `self._cache[k]=v` subscript writes →
  set_attr, `for` loops → `Fold`/match, augassign, composition threading) — each mechanical (the rules
  already do `Let`/`Fold`), but unbuilt. Whole-method FULLY-mechanical stays 2.4% (mixing-limited, the
  wrong unit). HONEST STATE: the ceiling is ~80% (the code's shape), the built tool is at 11%, and the
  remaining work is (a) the mechanical long-tail (engineering, bounded) + (b) the ~80 REVIEW judgment
  faculties (the worklist). The shape is straightforward; the tool just hasn't been ground to the
  ceiling yet.
- **Migrator finalised + the PIVOT to agent self-reorganisation (2026-06-17):** `body_term` (compose
  the WHOLE method body via the rules' block porter — local `x=`→Let, `for`→Fold, `if`→IfThenElse)
  added, then combined: a clean single-return composes its return expression (fast); a multi-statement
  pure-value body composes whole (absorbing its statements); a side-effecting statement stays residual.
  That's the migrator at its best honest state. CREATOR'S DIRECTION: stop hand-driving the migration
  with assistant scripts — "move to domains, and at that point it is probably better to have
  jabberwock REORGANISE ITSELF." The whole session built the agent's own faculties for exactly this:
  consume/distribution/worklist (it surveys its Python and sees its shape) + AST→Term rules + `tick`
  (it folds mechanical code into Terms) + Layer B `self_extend` (it mints missing primitives) + the
  keystone `self_modification` (it edits/rebuilds its own source, guarded) + its frontier/gap selector
  (it picks what to reorganise). NEXT PHASE: wire these into an agent-driven self-reorganisation loop
  over `domains/` + `curious_agent` — the agent ports the mechanical bulk, mints what it lacks,
  expresses the decision faculties as Rules, verifies — with the assistant as world-adapter, not
  migrator. The project's own thesis applied to itself: the agent knows its shape, so it re-shapes.
- **Domains phase begun — the agent surveys its whole layer (2026-06-17):** `domains/self_reorganize.py`
  is the agent's self-reorganisation SURVEY faculty (reusing the worklist classifier; the rules +
  migrator do the per-module porting). Over ALL **448 domains/ files, 4993 defs (161k lines)**: after
  correcting the classifier's overcount (a `REVIEW` def with no `self` reference is PURE compute that
  ports via the rules, not judgment — the SAME static-vs-real trap, caught and fixed: 62.5%→6.3%
  judgment), the shape is **~85% mechanical** (PURE 56% + RULE 15% + GRAPH-BUILD 9% + PRIMITIVE 4% +
  FACTORY 2%), 7% composition glue, **6.3% (313 defs) genuine judgment**, 2% I/O. The whole codebase
  has the SAME shape as `curious_agent`: a mechanical bulk the migrator transcribes + a small bounded
  judgment core. Judgment hotspots (where the agent's frontier selector looks first): `curious_agent`
  (79), `code_writing_cortex` (15), `concurrency` (15), `elevator` (11), `llm_partner` (9), … The
  161k-line "delete the Python agent" migration is, across the whole layer, ~85% mechanical
  transcription + ~313 decision defs to express as Rules — bounded, and exactly the agent's job.
- **EXECUTED the agent reorganisation on real modules — the recursive-web finding (2026-06-17):**
  `self_reorganize.reorganize_module(path)` runs the migrator over a module, producing real
  engine-accepted Rules + Terms. On `feature_generator` (13) and `contextualization_depth` (21): each
  yielded 1 engine-accepted Rule and ~12–20 residual — far below the static "mechanical-class" count.
  The residual is NOT difficulty: methods like `salience` = `_sal.salience(_care_signature(artifact))`
  and `cheap_shape` (build a dict from concept reads) are CROSS-FACULTY COMPOSITION — they delegate to
  OTHER faculties/modules. So the codebase is a RECURSIVE WEB of faculties calling faculties, not
  independent methods. The migrator ports the LEAVES; composition methods become Rules that invoke
  sub-Rules, which resolves HOLISTICALLY once the leaves are migrated — not per-isolated-method. That
  reconciles the last gap: static shape ~85% mechanical (true), per-isolated-method built-yield low
  (because methods compose, not because they're hard). The migration is therefore a HOLISTIC
  re-expression of the faculty web as inter-referencing Rules — leaves first (the migrator does these
  mechanically), then the composition glue resolves as the leaves become referenceable — exactly an
  agent-driven, frontier-ordered job (migrate a leaf, its callers' references resolve, repeat), with
  the assistant as world-adapter. The execution faculty exists and produces verified graph data; the
  remaining work is running it holistically over the web, leaf-inward, which is the agent's loop.

Two corrigibility guards from the cross-cutting section are now real: an append-only audit of every
self-modification (`var/self_mod_audit.log`), and the daemon's checkpoint-before-restart (a bad
self-change reverts via rollback; a bad rebuild never installs).

*Net: the agent can now safely modify every layer of itself — graph (already), its Python (live edit,
verified; and move-native for pure compute-cores, verified faithful), and its Rust: both EDIT existing
source (guarded, rebuild) AND ADD a new native primitive end-to-end (B, verified —
specify→emit→apply→check→build→call, all-or-nothing). All four layers (A/B/C + keystone) are
demonstrated and committed. The standing limit is honest and bounded: the move-native map handles
simple expression cores only — complex Python (control flow, comprehensions, mutation) is refused as a
named residual and stays a graph Rule or routes to B, which is exactly where CLAUDE.md wants it.*
